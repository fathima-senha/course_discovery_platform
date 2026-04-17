from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.accounts.models import StudentProfile
from apps.courses.models import Course


class Enrollment(models.Model):
    """
    Tracks a student's enrollment in a course.
    Enforces no duplicate enrollments via unique_together.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"
        EXPIRED = "expired", "Expired"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    progress_pct = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enrollment"
        unique_together = ("student", "course")  # Prevents duplicate enrollments
        ordering = ["-enrolled_at"]
        indexes = [
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.user.email} → {self.course.title}"

    def mark_complete(self):
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.progress_pct = 100.0
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "progress_pct", "completed_at"])


class Wishlist(models.Model):
    """
    Allows students to save courses they're interested in.
    unique_together prevents a student from saving the same course twice.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "wishlist"
        unique_together = ("student", "course")  # Prevents duplicate wishlist entries
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.student.user.email} → {self.course.title} (wishlist)"


class Review(models.Model):
    """
    Student review and rating for an enrolled course.
    Only enrolled students can submit a review (enforced at the view level).
    unique_together ensures one review per student per course.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "review"
        unique_together = ("student", "course")  # One review per student per course
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course", "is_approved"]),
        ]

    def __str__(self):
        return f"{self.student.user.email} rated {self.course.title}: {self.rating}/5"

    def clean(self):
        """Ensure the student is actually enrolled before reviewing."""
        enrolled = Enrollment.objects.filter(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        ).exists()
        if not enrolled:
            raise ValidationError("Only enrolled students can leave a review.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Recalculate course avg_rating after save
        self._update_course_rating()

    def _update_course_rating(self):
        from django.db.models import Avg, Count
        stats = Review.objects.filter(
            course=self.course, is_approved=True
        ).aggregate(avg=Avg("rating"), count=Count("id"))
        self.course.avg_rating = round(stats["avg"] or 0.0, 2)
        self.course.review_count = stats["count"]
        self.course.save(update_fields=["avg_rating", "review_count"])