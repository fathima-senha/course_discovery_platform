from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum

from apps.accounts.models import StudentProfile, ProviderProfile
from apps.courses.models import Course, Category, Tag
from apps.interactions.models import Enrollment, Review
from apps.payments.models import Payment
from .forms import CategoryForm, TagForm

User = get_user_model()


# ─── Permission Helper ────────────────────────────────────────────────────────

class AdminRequiredMixin:
    """
    Mixin that checks if the logged-in user is an admin.
    Add this to every admin view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admins only.')
            return redirect('landing')
        return super().dispatch(request, *args, **kwargs)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class AdminDashboardView(AdminRequiredMixin, View):
    """
    GET /admin-panel/dashboard/
    Shows platform-wide stats.
    """
    def get(self, request):
        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        stats = {
            'total_users':           User.objects.count(),
            'total_students':        User.objects.filter(role='student').count(),
            'total_providers':       User.objects.filter(role='provider').count(),
            'total_courses':         Course.objects.count(),
            'published_courses':     Course.objects.filter(is_published=True).count(),
            'draft_courses':         Course.objects.filter(is_published=False).count(),
            'total_enrollments':     Enrollment.objects.count(),
            'total_reviews':         Review.objects.count(),
            'pending_reviews':       Review.objects.filter(is_approved=False).count(),
            'total_payments':        Payment.objects.filter(status='completed').count(),
            'total_revenue':         total_revenue,
            'unverified_providers':  ProviderProfile.objects.filter(is_verified=False).count(),
        }

        # Recent activity
        recent_users       = User.objects.order_by('-created_at')[:5]
        recent_enrollments = Enrollment.objects.select_related(
            'student__user', 'course'
        ).order_by('-enrolled_at')[:5]

        return render(request, 'adminpanel/dashboard.html', {
            'stats':              stats,
            'recent_users':       recent_users,
            'recent_enrollments': recent_enrollments,
        })


# ─── User Management ─────────────────────────────────────────────────────────

class AdminUserListView(AdminRequiredMixin, View):
    """
    GET /admin-panel/users/
    Lists all users. Filter by role using ?role=student etc.
    """
    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        role  = request.GET.get('role')
        if role:
            users = users.filter(role=role)
        search = request.GET.get('q')
        if search:
            users = users.filter(email__icontains=search)
        return render(request, 'adminpanel/users.html', {
            'users':  users,
            'role':   role,
            'search': search,
        })


class AdminUserDetailView(AdminRequiredMixin, View):
    """
    GET /admin-panel/users/<int:pk>/
    Shows details of a single user.
    """
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, 'adminpanel/user_detail.html', {'user': user})


class AdminToggleUserActiveView(AdminRequiredMixin, View):
    """
    POST /admin-panel/users/<int:pk>/toggle-active/
    Activates or deactivates a user account.
    """
    def post(self, request, pk):
        user          = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.email} has been {state}.')
        return redirect('admin_users')


class AdminDeleteUserView(AdminRequiredMixin, View):
    """
    POST /admin-panel/users/<int:pk>/delete/
    Deletes a user account permanently.
    """
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        email = user.email
        user.delete()
        messages.success(request, f'User {email} deleted successfully.')
        return redirect('admin_users')


# ─── Provider Verification ────────────────────────────────────────────────────

class AdminProviderListView(AdminRequiredMixin, View):
    """
    GET /admin-panel/providers/
    Lists all providers. Filter by ?verified=true or ?verified=false.
    """
    def get(self, request):
        providers = ProviderProfile.objects.select_related('user').all()
        verified  = request.GET.get('verified')
        if verified == 'true':
            providers = providers.filter(is_verified=True)
        elif verified == 'false':
            providers = providers.filter(is_verified=False)
        return render(request, 'adminpanel/providers.html', {
            'providers': providers,
            'verified':  verified,
        })


class AdminVerifyProviderView(AdminRequiredMixin, View):
    """
    POST /admin-panel/providers/<int:pk>/verify/
    Toggles provider verification status.
    """
    def post(self, request, pk):
        from django.utils import timezone
        provider             = get_object_or_404(ProviderProfile, pk=pk)
        provider.is_verified = not provider.is_verified
        provider.verified_at = timezone.now() if provider.is_verified else None
        provider.save(update_fields=['is_verified', 'verified_at'])
        state = 'verified' if provider.is_verified else 'unverified'
        messages.success(request, f'{provider.company_name} has been {state}.')
        return redirect('admin_providers')


# ─── Course Management ────────────────────────────────────────────────────────

class AdminCourseListView(AdminRequiredMixin, View):
    """
    GET /admin-panel/courses/
    Lists all courses including drafts.
    """
    def get(self, request):
        courses = Course.objects.select_related(
            'provider__user'
        ).order_by('-created_at')
        status = request.GET.get('status')
        if status == 'published':
            courses = courses.filter(is_published=True)
        elif status == 'draft':
            courses = courses.filter(is_published=False)
        search = request.GET.get('q')
        if search:
            courses = courses.filter(title__icontains=search)
        return render(request, 'adminpanel/courses.html', {
            'courses': courses,
            'status':  status,
        })


class AdminToggleCoursePublishView(AdminRequiredMixin, View):
    """
    POST /admin-panel/courses/<int:pk>/toggle-publish/
    Admin publishes or unpublishes any course.
    """
    def post(self, request, pk):
        from django.utils import timezone
        course              = get_object_or_404(Course, pk=pk)
        course.is_published = not course.is_published
        course.status       = 'published' if course.is_published else 'draft'
        course.published_at = timezone.now() if course.is_published else None
        course.save(update_fields=['is_published', 'status', 'published_at'])
        state = 'published' if course.is_published else 'unpublished'
        messages.success(request, f'Course "{course.title}" has been {state}.')
        return redirect('admin_courses')


class AdminDeleteCourseView(AdminRequiredMixin, View):
    """
    POST /admin-panel/courses/<int:pk>/delete/
    Admin deletes any course.
    """
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        title  = course.title
        course.delete()
        messages.success(request, f'Course "{title}" deleted successfully.')
        return redirect('admin_courses')


# ─── Review Moderation ────────────────────────────────────────────────────────

class AdminReviewListView(AdminRequiredMixin, View):
    """
    GET /admin-panel/reviews/
    Lists all reviews. Filter by ?approved=false for pending reviews.
    """
    def get(self, request):
        reviews  = Review.objects.select_related(
            'student__user', 'course'
        ).order_by('-created_at')
        approved = request.GET.get('approved')
        if approved == 'false':
            reviews = reviews.filter(is_approved=False)
        elif approved == 'true':
            reviews = reviews.filter(is_approved=True)
        return render(request, 'adminpanel/reviews.html', {
            'reviews':  reviews,
            'approved': approved,
        })


class AdminApproveReviewView(AdminRequiredMixin, View):
    """
    POST /admin-panel/reviews/<int:pk>/approve/
    Toggles review approval status.
    """
    def post(self, request, pk):
        review             = get_object_or_404(Review, pk=pk)
        review.is_approved = not review.is_approved
        review.save(update_fields=['is_approved'])
        state = 'approved' if review.is_approved else 'unapproved'
        messages.success(request, f'Review has been {state}.')
        return redirect('admin_reviews')


class AdminDeleteReviewView(AdminRequiredMixin, View):
    """
    POST /admin-panel/reviews/<int:pk>/delete/
    Admin deletes any review.
    """
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('admin_reviews')


# ─── Payment Overview ─────────────────────────────────────────────────────────

class AdminPaymentListView(AdminRequiredMixin, View):
    """
    GET /admin-panel/payments/
    Lists all payments across the platform.
    """
    def get(self, request):
        payments = Payment.objects.select_related(
            'student__user', 'course'
        ).order_by('-created_at')
        status = request.GET.get('status')
        if status:
            payments = payments.filter(status=status)

        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        return render(request, 'adminpanel/payments.html', {
            'payments':      payments,
            'status':        status,
            'total_revenue': total_revenue,
        })


# ─── Category Management ──────────────────────────────────────────────────────

class AdminCategoryListView(AdminRequiredMixin, View):
    """
    GET  /admin-panel/categories/        — list all categories
    POST /admin-panel/categories/        — create new category
    """
    def get(self, request):
        categories = Category.objects.all().order_by('name')
        form       = CategoryForm()
        return render(request, 'adminpanel/categories.html', {
            'categories': categories,
            'form':       form,
        })

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('admin_categories')
        categories = Category.objects.all().order_by('name')
        return render(request, 'adminpanel/categories.html', {
            'categories': categories,
            'form':       form,
        })


class AdminDeleteCategoryView(AdminRequiredMixin, View):
    """
    POST /admin-panel/categories/<int:pk>/delete/
    Deletes a category.
    """
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('admin_categories')


# ─── Tag Management ───────────────────────────────────────────────────────────

class AdminTagListView(AdminRequiredMixin, View):
    """
    GET  /admin-panel/tags/   — list all tags
    POST /admin-panel/tags/   — create new tag
    """
    def get(self, request):
        tags = Tag.objects.all().order_by('name')
        form = TagForm()
        return render(request, 'adminpanel/tags.html', {
            'tags': tags,
            'form': form,
        })

    def post(self, request):
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully!')
            return redirect('admin_tags')
        tags = Tag.objects.all().order_by('name')
        return render(request, 'adminpanel/tags.html', {
            'tags': tags,
            'form': form,
        })


class AdminDeleteTagView(AdminRequiredMixin, View):
    """
    POST /admin-panel/tags/<int:pk>/delete/
    Deletes a tag.
    """
    def post(self, request, pk):
        tag = get_object_or_404(Tag, pk=pk)
        tag.delete()
        messages.success(request, 'Tag deleted.')
        return redirect('admin_tags')