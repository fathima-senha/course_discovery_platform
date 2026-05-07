from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q

from .models import Course, Category, Tag
from .forms import CourseForm
from apps.accounts.models import ProviderProfile


# ─── Public Views (no login needed) ─────────────────────────────────────────

class CourseListView(View):
    """
    GET /courses/
    Shows all published courses with search and filtering.
    Anyone can view this page.
    """
    def get(self, request):
        courses    = Course.objects.filter(is_published=True).select_related('provider')
        categories = Category.objects.filter(parent=None)
        tags       = Tag.objects.all()

        # Search
        q = request.GET.get('q')
        if q:
            courses = courses.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()

        # Filter by category
        category = request.GET.get('category')
        if category:
            courses = courses.filter(categories__slug=category)

        # Filter by level
        level = request.GET.get('level')
        if level:
            courses = courses.filter(level=level)

        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            courses = courses.filter(price__gte=min_price)
        if max_price:
            courses = courses.filter(price__lte=max_price)

        # Filter by rating
        min_rating = request.GET.get('min_rating')
        if min_rating:
            courses = courses.filter(avg_rating__gte=min_rating)

        # Sorting
        ordering = request.GET.get('ordering', '-created_at')
        allowed  = ['price', '-price', 'avg_rating', '-avg_rating', '-created_at']
        if ordering in allowed:
            courses = courses.order_by(ordering)

        return render(request, 'courses/listing.html', {
            'courses':    courses,
            'categories': categories,
            'tags':       tags,
            'q':          q,
        })


class CourseDetailView(View):
    """
    GET /courses/<int:pk>/
    Shows full details of a single course.
    Anyone can view this page.
    """
    def get(self, request, pk):
        course  = get_object_or_404(Course, pk=pk, is_published=True)
        reviews = course.reviews.filter(is_approved=True).select_related('student__user')

        # Check if student is already enrolled
        is_enrolled  = False
        in_wishlist  = False
        if request.user.is_authenticated and request.user.role == 'student':
            profile     = request.user.student_profile
            is_enrolled = profile.enrollments.filter(course=course).exists()
            in_wishlist = profile.wishlist.filter(course=course).exists()

        return render(request, 'courses/detail.html', {
            'course':      course,
            'reviews':     reviews,
            'is_enrolled': is_enrolled,
            'in_wishlist': in_wishlist,
        })


class CategoryCourseListView(View):
    """
    GET /courses/category/<slug>/
    Shows all courses in a specific category.
    """
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        courses  = Course.objects.filter(
            categories=category,
            is_published=True,
        ).select_related('provider')
        return render(request, 'courses/category.html', {
            'category': category,
            'courses':  courses,
        })


# ─── Provider Course Management (login required) ─────────────────────────────

@method_decorator(login_required, name='dispatch')
class ProviderDashboardView(View):
    """
    GET /provider/dashboard/
    Shows provider dashboard with their course stats.
    """
    def get(self, request):
        if request.user.role != 'provider':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        provider  = request.user.provider_profile
        courses   = Course.objects.filter(provider=provider)
        published = courses.filter(is_published=True).count()
        drafts    = courses.filter(is_published=False).count()
        total_enrollments = sum(c.enrollment_count for c in courses)

        return render(request, 'courses/provider_dashboard.html', {
            'provider':          provider,
            'courses':           courses,
            'published':         published,
            'drafts':            drafts,
            'total_enrollments': total_enrollments,
        })


@method_decorator(login_required, name='dispatch')
class MyCourseListView(View):
    """
    GET /provider/courses/
    Shows all courses created by the logged-in provider.
    """
    def get(self, request):
        if request.user.role != 'provider':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        provider = request.user.provider_profile
        status   = request.GET.get('status')
        courses  = Course.objects.filter(provider=provider).order_by('-created_at')
        if status == 'published':
            courses = courses.filter(is_published=True)
        elif status == 'draft':
            courses = courses.filter(is_published=False)
        return render(request, 'courses/my_courses.html', {
            'courses': courses,
            'status':  status,
        })


@method_decorator(login_required, name='dispatch')
class CourseCreateView(View):
    """
    GET  /provider/courses/create/  — shows create course form
    POST /provider/courses/create/  — saves new course
    """
    def get(self, request):
        if request.user.role != 'provider':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        form = CourseForm()
        return render(request, 'courses/create_course.html', {'form': form})

    def post(self, request):
        if request.user.role != 'provider':
            return redirect('landing')
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course          = form.save(commit=False)
            course.provider = request.user.provider_profile
            course.save()
            form.save_m2m()
            messages.success(request, 'Course created successfully!')
            return redirect('my_courses')
        return render(request, 'courses/create_course.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class CourseEditView(View):
    """
    GET  /provider/courses/<int:pk>/edit/  — shows edit form
    POST /provider/courses/<int:pk>/edit/  — saves changes
    """
    def get(self, request, pk):
        if request.user.role != 'provider':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        provider = request.user.provider_profile
        course   = get_object_or_404(Course, pk=pk, provider=provider)
        form     = CourseForm(instance=course)
        return render(request, 'courses/edit_course.html', {
            'form': form, 'course': course,
        })

    def post(self, request, pk):
        if request.user.role != 'provider':
            return redirect('landing')
        provider = request.user.provider_profile
        course   = get_object_or_404(Course, pk=pk, provider=provider)
        form     = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('my_courses')
        return render(request, 'courses/edit_course.html', {
            'form': form, 'course': course,
        })


@method_decorator(login_required, name='dispatch')
class CourseDeleteView(View):
    """
    POST /provider/courses/<int:pk>/delete/
    Deletes a course. Only the owning provider can do this.
    """
    def post(self, request, pk):
        if request.user.role != 'provider':
            return redirect('landing')
        provider = request.user.provider_profile
        course   = get_object_or_404(Course, pk=pk, provider=provider)
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('my_courses')


@method_decorator(login_required, name='dispatch')
class CoursePublishToggleView(View):
    """
    POST /provider/courses/<int:pk>/publish/
    Toggles course between published and draft.
    """
    def post(self, request, pk):
        if request.user.role != 'provider':
            return redirect('landing')
        provider           = request.user.provider_profile
        course             = get_object_or_404(Course, pk=pk, provider=provider)
        course.is_published = not course.is_published
        course.status      = 'published' if course.is_published else 'draft'
        course.save(update_fields=['is_published', 'status'])
        state = 'published' if course.is_published else 'unpublished'
        messages.success(request, f'Course {state} successfully!')
        return redirect('my_courses')
    