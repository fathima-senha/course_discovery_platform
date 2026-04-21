from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Course, Category, Tag
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    CategorySerializer,
    TagSerializer,
)
from .filters import CourseFilter
from .pagination import CoursePagination
from apps.accounts.models import ProviderProfile


# ─── Permission Helper ───────────────────────────────────────────────────────

def is_provider(user):
    return user.is_authenticated and user.role == "provider"


# ─── Category Views ──────────────────────────────────────────────────────────

class CategoryListView(APIView):
    """
    GET /api/courses/categories/
    Returns all top-level categories with their subcategories.
    Public — no login required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.filter(parent=None).prefetch_related("subcategories")
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryDetailView(APIView):
    """
    GET /api/courses/categories/<int:pk>/
    Returns a single category and its subcategories.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            category = Category.objects.prefetch_related("subcategories").get(pk=pk)
        except Category.DoesNotExist:
            return Response(
                {"error": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Tag Views ───────────────────────────────────────────────────────────────

class TagListView(APIView):
    """
    GET /api/courses/tags/
    Returns all available tags.
    Public — no login required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Course Views ─────────────────────────────────────────────────────────────

class CourseListView(APIView):
    """
    GET /api/courses/
    Returns all published courses with filtering, searching and ordering.
    Supports:
      - ?q=python             full text search
      - ?level=beginner       filter by level
      - ?min_price=0          filter by price range
      - ?max_price=2000
      - ?category=web-development
      - ?tags=python,django
      - ?min_rating=4
      - ?ordering=price       sort by price, rating, created_at
    Public — no login required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Course.objects.filter(
            is_published=True
        ).select_related(
            "provider__user"
        ).prefetch_related(
            "categories", "tags"
        )

        # Apply filters
        filterset = CourseFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        # Apply ordering
        ordering = request.GET.get("ordering", "-created_at")
        allowed_ordering = ["price", "-price", "avg_rating", "-avg_rating", "created_at", "-created_at"]
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        # Apply pagination
        paginator = CoursePagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CourseListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CourseDetailView(APIView):
    """
    GET /api/courses/<int:pk>/
    Returns full details of a single published course.
    Public — no login required.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            course = Course.objects.select_related(
                "provider__user"
            ).prefetch_related(
                "categories", "tags", "reviews"
            ).get(pk=pk, is_published=True)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CourseDetailSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CourseCreateView(APIView):
    """
    POST /api/courses/create/
    Providers can create a new course.
    Only providers can access this.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_provider(request.user):
            return Response(
                {"error": "Only providers can create courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            provider = ProviderProfile.objects.get(user=request.user)
        except ProviderProfile.DoesNotExist:
            return Response(
                {"error": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CourseCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(provider=provider)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseUpdateView(APIView):
    """
    PUT   /api/courses/<int:pk>/edit/  — update a course
    DELETE /api/courses/<int:pk>/edit/ — delete a course
    Only the provider who owns the course can update or delete it.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            provider = ProviderProfile.objects.get(user=user)
            return Course.objects.get(pk=pk, provider=provider)
        except (Course.DoesNotExist, ProviderProfile.DoesNotExist):
            return None

    def put(self, request, pk):
        if not is_provider(request.user):
            return Response(
                {"error": "Only providers can edit courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course = self.get_object(pk, request.user)
        if not course:
            return Response(
                {"error": "Course not found or you do not own this course."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CourseCreateUpdateSerializer(
            course, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not is_provider(request.user):
            return Response(
                {"error": "Only providers can delete courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course = self.get_object(pk, request.user)
        if not course:
            return Response(
                {"error": "Course not found or you do not own this course."},
                status=status.HTTP_404_NOT_FOUND,
            )
        course.delete()
        return Response(
            {"message": "Course deleted successfully."},
            status=status.HTTP_200_OK,
        )


class ProviderCourseListView(APIView):
    """
    GET /api/courses/my-courses/
    Returns all courses created by the logged-in provider
    including drafts and unpublished ones.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_provider(request.user):
            return Response(
                {"error": "Only providers can access this."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            provider = ProviderProfile.objects.get(user=request.user)
        except ProviderProfile.DoesNotExist:
            return Response(
                {"error": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        courses = Course.objects.filter(provider=provider).order_by("-created_at")
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoursePublishView(APIView):
    """
    POST /api/courses/<int:pk>/publish/
    Toggles a course between published and draft.
    Only the owning provider can do this.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_provider(request.user):
            return Response(
                {"error": "Only providers can publish courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            provider = ProviderProfile.objects.get(user=request.user)
            course = Course.objects.get(pk=pk, provider=provider)
        except (Course.DoesNotExist, ProviderProfile.DoesNotExist):
            return Response(
                {"error": "Course not found or you do not own this course."},
                status=status.HTTP_404_NOT_FOUND,
            )
        from django.utils import timezone
        course.is_published = not course.is_published
        course.status = "published" if course.is_published else "draft"
        course.published_at = timezone.now() if course.is_published else None
        course.save(update_fields=["is_published", "status", "published_at"])
        return Response(
            {
                "message": f"Course {'published' if course.is_published else 'unpublished'} successfully.",
                "is_published": course.is_published,
            },
            status=status.HTTP_200_OK,
        )