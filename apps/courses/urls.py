from django.urls import path
from .views import (
    CourseListView,
    CourseDetailView,
    CategoryCourseListView,
    ProviderDashboardView,
    MyCourseListView,
    CourseCreateView,
    CourseEditView,
    CourseDeleteView,
    CoursePublishToggleView,
)
 
urlpatterns = [
    # Public
    path('',                                CourseListView.as_view(),           name='course_list'),
    path('<int:pk>/',                       CourseDetailView.as_view(),         name='course_detail'),
    path('category/<slug:slug>/',           CategoryCourseListView.as_view(),   name='category_courses'),
 
    # Provider
    path('provider/dashboard/',             ProviderDashboardView.as_view(),    name='provider_dashboard'),
    path('provider/courses/',               MyCourseListView.as_view(),         name='my_courses'),
    path('provider/courses/create/',        CourseCreateView.as_view(),         name='course_create'),
    path('provider/courses/<int:pk>/edit/', CourseEditView.as_view(),           name='course_edit'),
    path('provider/courses/<int:pk>/delete/', CourseDeleteView.as_view(),       name='course_delete'),
    path('provider/courses/<int:pk>/publish/', CoursePublishToggleView.as_view(), name='course_publish'),
]