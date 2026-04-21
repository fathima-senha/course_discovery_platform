from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    TagListView,
    CourseListView,
    CourseDetailView,
    CourseCreateView,
    CourseUpdateView,
    ProviderCourseListView,
    CoursePublishView,
)
 
urlpatterns = [
    # Categories & Tags
    path("categories/",                 CategoryListView.as_view(),     name="category_list"),
    path("categories/<int:pk>/",        CategoryDetailView.as_view(),   name="category_detail"),
    path("tags/",                       TagListView.as_view(),          name="tag_list"),
 
    # Course browsing (public)
    path("",                            CourseListView.as_view(),       name="course_list"),
    path("<int:pk>/",                   CourseDetailView.as_view(),     name="course_detail"),
 
    # Provider course management
    path("create/",                     CourseCreateView.as_view(),     name="course_create"),
    path("<int:pk>/edit/",              CourseUpdateView.as_view(),     name="course_update"),
    path("<int:pk>/publish/",           CoursePublishView.as_view(),    name="course_publish"),
    path("my-courses/",                 ProviderCourseListView.as_view(), name="my_courses"),
]