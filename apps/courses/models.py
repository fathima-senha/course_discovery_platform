from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from apps.accounts.models import ProviderProfile


class Category(models.Model):
    """
    Hierarchical course categories (e.g. Technology > Web Development).
    Self-referential FK enables unlimited nesting depth.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # CSS icon class or emoji
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "category"
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    """
    Flat skill/technology tags for fine-grained filtering.
    e.g. "Python", "React", "Docker", "Machine Learning"
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        db_table = "tag"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Core course entity managed by providers.
    Stores all metadata needed for search, filtering, and display.
    """

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="courses",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    thumbnail = models.ImageField(upload_to="thumbnails/courses/", blank=True, null=True)

    # Pricing
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    is_free = models.BooleanField(default=False)
    discount_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )

    # Classification
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    categories = models.ManyToManyField(
        "Category",
        through="CourseCategory",
        related_name="courses",
    )
    tags = models.ManyToManyField(
        "Tag",
        through="CourseTag",
        related_name="courses",
    )

    # Duration
    duration_hours = models.PositiveIntegerField(default=0, help_text="Total hours of content")
    duration_weeks = models.PositiveIntegerField(default=0, help_text="Estimated weeks to complete")

    # Aggregates (updated via signals or periodic tasks)
    avg_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        db_index=True,
    )
    review_count = models.PositiveIntegerField(default=0)
    enrollment_count = models.PositiveIntegerField(default=0)

    # Status & visibility
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_published = models.BooleanField(default=False, db_index=True)
    language = models.CharField(max_length=50, default="English")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "course"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["level", "is_published"]),
            models.Index(fields=["price", "is_published"]),
            models.Index(fields=["avg_rating", "is_published"]),
            models.Index(fields=["duration_hours", "is_published"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.price == 0:
            self.is_free = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def effective_price(self):
        """Returns the discounted price if available, else regular price."""
        return self.discount_price if self.discount_price else self.price


class CourseCategory(models.Model):
    """
    Explicit through table for Course <-> Category M2M.
    Allows a course to appear in multiple categories.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)  # One category can be marked primary

    class Meta:
        db_table = "course_category"
        unique_together = ("course", "category")
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"

    def __str__(self):
        return f"{self.course.title} → {self.category.name}"


class CourseTag(models.Model):
    """
    Explicit through table for Course <-> Tag M2M.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "course_tag"
        unique_together = ("course", "tag")
        verbose_name = "Course Tag"

    def __str__(self):
        return f"{self.course.title} → {self.tag.name}"