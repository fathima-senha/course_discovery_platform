from rest_framework import serializers
from .models import Course, Category, Tag, CourseCategory, CourseTag


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "subcategories"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CourseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for course listing page.
    Shows just enough info for a course card.
    """
    provider_name = serializers.CharField(
        source="provider.company_name", read_only=True
    )
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "short_description",
            "thumbnail", "price", "discount_price", "effective_price",
            "is_free", "level", "duration_hours",
            "avg_rating", "review_count", "enrollment_count",
            "provider_name", "categories", "tags",
            "is_published", "created_at",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for course detail page.
    Includes everything including full description.
    """
    provider_name = serializers.CharField(
        source="provider.company_name", read_only=True
    )
    provider_id = serializers.IntegerField(
        source="provider.id", read_only=True
    )
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "short_description",
            "thumbnail", "price", "discount_price", "effective_price",
            "is_free", "level", "duration_hours", "duration_weeks",
            "avg_rating", "review_count", "enrollment_count",
            "provider_id", "provider_name",
            "categories", "tags", "language",
            "is_published", "created_at", "published_at",
        ]


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Used when a provider creates or edits a course.
    Accepts category and tag IDs to link them.
    """
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Course
        fields = [
            "title", "description", "short_description",
            "thumbnail", "price", "discount_price",
            "level", "duration_hours", "duration_weeks",
            "language", "category_ids", "tag_ids",
        ]

    def create(self, validated_data):
        category_ids = validated_data.pop("category_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        course = Course.objects.create(**validated_data)
        self._set_categories(course, category_ids)
        self._set_tags(course, tag_ids)
        return course

    def update(self, instance, validated_data):
        category_ids = validated_data.pop("category_ids", None)
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if category_ids is not None:
            CourseCategory.objects.filter(course=instance).delete()
            self._set_categories(instance, category_ids)
        if tag_ids is not None:
            CourseTag.objects.filter(course=instance).delete()
            self._set_tags(instance, tag_ids)
        return instance

    def _set_categories(self, course, category_ids):
        for i, cat_id in enumerate(category_ids):
            try:
                category = Category.objects.get(pk=cat_id)
                CourseCategory.objects.create(
                    course=course,
                    category=category,
                    is_primary=(i == 0),
                )
            except Category.DoesNotExist:
                pass

    def _set_tags(self, course, tag_ids):
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(pk=tag_id)
                CourseTag.objects.create(course=course, tag=tag)
            except Tag.DoesNotExist:
                pass