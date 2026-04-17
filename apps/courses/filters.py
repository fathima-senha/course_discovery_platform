"""
courses/filters.py  —  Advanced filtering for the Course Discovery Platform.

Uses django-filter to build a composable, URL-driven filter system.
Install: pip install django-filter

Add 'django_filters' to INSTALLED_APPS and
REST_FRAMEWORK = { 'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'] }
"""

import django_filters
from django.db.models import Q
from .models import Course


class CourseFilter(django_filters.FilterSet):
    """
    Filterset that powers the search & filtering system.
    All fields are optional; unset filters are ignored entirely.

    Example URL:
      /api/courses/?level=beginner&min_price=0&max_price=2000
                  &category=web-development&tags=python,django
                  &min_rating=4&max_duration=40&q=machine+learning
    """

    # Full-text search across title, description, and tags
    q = django_filters.CharFilter(method="filter_search", label="Search")

    # Price range
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    is_free = django_filters.BooleanFilter(field_name="is_free")

    # Duration (in hours)
    min_duration = django_filters.NumberFilter(field_name="duration_hours", lookup_expr="gte")
    max_duration = django_filters.NumberFilter(field_name="duration_hours", lookup_expr="lte")

    # Skill level
    level = django_filters.MultipleChoiceFilter(
        choices=Course.Level.choices,
        conjoined=False,  # OR across multiple levels
    )

    # Category (by slug, supports comma-separated values)
    category = django_filters.CharFilter(method="filter_category", label="Category slug")

    # Tags (comma-separated slugs; course must have ALL specified tags)
    tags = django_filters.CharFilter(method="filter_tags", label="Tag slugs (comma-separated)")

    # Minimum rating
    min_rating = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")

    # Provider
    provider = django_filters.NumberFilter(field_name="provider__id")

    # Language
    language = django_filters.CharFilter(field_name="language", lookup_expr="iexact")

    class Meta:
        model = Course
        fields = [
            "q", "level", "is_free",
            "min_price", "max_price",
            "min_duration", "max_duration",
            "min_rating", "category", "tags",
            "provider", "language",
        ]

    def filter_queryset(self, queryset):
        """Only surface published courses to end users."""
        return super().filter_queryset(queryset).filter(is_published=True)

    def filter_search(self, queryset, name, value):
        """
        Searches across title, short_description, and tag names.
        Uses OR logic so partial matches across fields are included.
        """
        return queryset.filter(
            Q(title__icontains=value)
            | Q(short_description__icontains=value)
            | Q(description__icontains=value)
            | Q(tags__name__icontains=value)
        ).distinct()

    def filter_category(self, queryset, name, value):
        """
        Filters by category slug. Includes courses in subcategories too
        so filtering by "technology" also returns "web-development" courses.
        """
        from .models import Category
        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()
        # Collect the category and all descendants
        cat_ids = self._get_descendant_ids(category)
        return queryset.filter(categories__id__in=cat_ids).distinct()

    def filter_tags(self, queryset, name, value):
        """
        Filters courses that have ALL of the given tag slugs.
        Input: comma-separated slugs e.g. "python,django,rest-api"
        """
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        for slug in slugs:
            queryset = queryset.filter(tags__slug=slug)
        return queryset.distinct()

    @staticmethod
    def _get_descendant_ids(category):
        """Recursively collects IDs of a category and all its children."""
        ids = [category.id]
        for child in category.subcategories.all():
            ids.extend(CourseFilter._get_descendant_ids(child))
        return ids


# ─── Optimized base queryset ────────────────────────────────────────────────

def get_course_queryset():
    """
    Returns a select_related + prefetch_related queryset optimized for
    the listing view. Use this as the base for all filtered views.
    """
    return (
        Course.objects
        .select_related("provider__user")
        .prefetch_related("categories", "tags")
        .filter(is_published=True)
    )