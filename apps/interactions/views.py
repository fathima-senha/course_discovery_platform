from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages

from .models import Enrollment, Wishlist, Review
from .forms import ReviewForm
from apps.courses.models import Course


# ─── Permission Helper ────────────────────────────────────────────────────────

def get_student(user):
    """Returns StudentProfile or None."""
    try:
        return user.student_profile
    except Exception:
        return None


# ─── Student Dashboard ────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class StudentDashboardView(View):
    """
    GET /student/dashboard/
    Shows the student dashboard with enrollments and wishlist summary.
    """
    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        student     = get_student(request.user)
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related('course').order_by('-enrolled_at')[:5]
        wishlist    = Wishlist.objects.filter(
            student=student
        ).select_related('course').order_by('-added_at')[:3]

        total_enrolled   = Enrollment.objects.filter(student=student).count()
        total_completed  = Enrollment.objects.filter(student=student, status='completed').count()
        total_inprogress = Enrollment.objects.filter(student=student, status='active').count()
        total_wishlist   = Wishlist.objects.filter(student=student).count()

        return render(request, 'interactions/student_dashboard.html', {
            'student':          student,
            'enrollments':      enrollments,
            'wishlist':         wishlist,
            'total_enrolled':   total_enrolled,
            'total_completed':  total_completed,
            'total_inprogress': total_inprogress,
            'total_wishlist':   total_wishlist,
        })


# ─── Enrollment Views ─────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class EnrollCourseView(View):
    """
    POST /interactions/enroll/<int:course_id>/
    Student enrolls in a course.
    After enrolling redirects back to the course detail page.
    """
    def post(self, request, course_id):
        if request.user.role != 'student':
            messages.error(request, 'Only students can enroll.')
            return redirect('course_detail', pk=course_id)
        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, 'You are already enrolled in this course.')
            return redirect('course_detail', pk=course_id)

        Enrollment.objects.create(student=student, course=course)
        Course.objects.filter(pk=course.pk).update(
            enrollment_count=course.enrollment_count + 1
        )
        messages.success(request, f'You are now enrolled in {course.title}!')
        return redirect('my_enrollments')


@method_decorator(login_required, name='dispatch')
class UnenrollCourseView(View):
    """
    POST /interactions/unenroll/<int:course_id>/
    Student drops a course.
    """
    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('landing')
        student    = get_student(request.user)
        enrollment = get_object_or_404(Enrollment, student=student, course_id=course_id)
        enrollment.status = 'dropped'
        enrollment.save(update_fields=['status'])
        messages.success(request, 'You have unenrolled from the course.')
        return redirect('my_enrollments')


@method_decorator(login_required, name='dispatch')
class MyEnrollmentsView(View):
    """
    GET /interactions/enrollments/
    Shows all courses the student is enrolled in.
    """
    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        student     = get_student(request.user)
        status      = request.GET.get('status')
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related('course__provider').order_by('-enrolled_at')

        if status in ['active', 'completed', 'dropped']:
            enrollments = enrollments.filter(status=status)

        return render(request, 'interactions/enrollments.html', {
            'enrollments': enrollments,
            'status':      status,
        })


@method_decorator(login_required, name='dispatch')
class UpdateProgressView(View):
    """
    POST /interactions/enroll/<int:course_id>/progress/
    Student updates their progress in a course.
    """
    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('landing')
        student    = get_student(request.user)
        enrollment = get_object_or_404(
            Enrollment, student=student,
            course_id=course_id, status='active'
        )
        progress = request.POST.get('progress_pct', 0)
        try:
            progress = float(progress)
            if not 0 <= progress <= 100:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid progress value.')
            return redirect('my_enrollments')

        enrollment.progress_pct = progress
        if progress == 100:
            enrollment.mark_complete()
            messages.success(request, 'Congratulations! Course marked as completed!')
        else:
            enrollment.save(update_fields=['progress_pct'])
            messages.success(request, 'Progress updated!')
        return redirect('my_enrollments')


# ─── Wishlist Views ───────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class WishlistView(View):
    """
    GET /interactions/wishlist/
    Shows all courses in the student's wishlist.
    """
    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        student  = get_student(request.user)
        wishlist = Wishlist.objects.filter(
            student=student
        ).select_related('course__provider').order_by('-added_at')
        return render(request, 'interactions/wishlist.html', {
            'wishlist': wishlist,
        })


@method_decorator(login_required, name='dispatch')
class WishlistAddView(View):
    """
    POST /interactions/wishlist/add/<int:course_id>/
    Adds a course to the student's wishlist.
    """
    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('course_detail', pk=course_id)
        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        if Wishlist.objects.filter(student=student, course=course).exists():
            messages.warning(request, 'Course is already in your wishlist.')
        else:
            Wishlist.objects.create(student=student, course=course)
            messages.success(request, f'{course.title} added to wishlist!')
        return redirect('course_detail', pk=course_id)


@method_decorator(login_required, name='dispatch')
class WishlistRemoveView(View):
    """
    POST /interactions/wishlist/remove/<int:course_id>/
    Removes a course from the wishlist.
    """
    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('landing')
        student = get_student(request.user)
        wishlist_item = Wishlist.objects.filter(
            student=student, course_id=course_id
        ).first()
        if wishlist_item:
            wishlist_item.delete()
            messages.success(request, 'Course removed from wishlist.')
        return redirect('wishlist')


# ─── Review Views ─────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class WriteReviewView(View):
    """
    GET  /interactions/courses/<int:course_id>/review/  — shows review form
    POST /interactions/courses/<int:course_id>/review/  — saves review
    Only enrolled students can write a review.
    """
    def get(self, request, course_id):
        if request.user.role != 'student':
            messages.error(request, 'Only students can write reviews.')
            return redirect('course_detail', pk=course_id)
        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        # Check enrollment
        if not Enrollment.objects.filter(student=student, course=course).exists():
            messages.error(request, 'You must be enrolled to write a review.')
            return redirect('course_detail', pk=course_id)

        # Check already reviewed
        if Review.objects.filter(student=student, course=course).exists():
            messages.warning(request, 'You have already reviewed this course.')
            return redirect('course_detail', pk=course_id)

        form = ReviewForm()
        return render(request, 'interactions/write_review.html', {
            'form': form, 'course': course,
        })

    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('landing')
        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        if not Enrollment.objects.filter(student=student, course=course).exists():
            messages.error(request, 'You must be enrolled to write a review.')
            return redirect('course_detail', pk=course_id)

        if Review.objects.filter(student=student, course=course).exists():
            messages.warning(request, 'You have already reviewed this course.')
            return redirect('course_detail', pk=course_id)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review         = form.save(commit=False)
            review.student = student
            review.course  = course
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('course_detail', pk=course_id)
        return render(request, 'interactions/write_review.html', {
            'form': form, 'course': course,
        })


@method_decorator(login_required, name='dispatch')
class DeleteReviewView(View):
    """
    POST /interactions/reviews/<int:pk>/delete/
    Student deletes their own review.
    """
    def post(self, request, pk):
        if request.user.role != 'student':
            return redirect('landing')
        student = get_student(request.user)
        review  = get_object_or_404(Review, pk=pk, student=student)
        course_id = review.course.pk
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('course_detail', pk=course_id)