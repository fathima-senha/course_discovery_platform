from django.urls import path
from .views import (
    AdminDashboardView,
    AdminUserListView,
    AdminUserDetailView,
    AdminToggleUserActiveView,
    AdminDeleteUserView,
    AdminProviderListView,
    AdminVerifyProviderView,
    AdminCourseListView,
    AdminToggleCoursePublishView,
    AdminDeleteCourseView,
    AdminReviewListView,
    AdminApproveReviewView,
    AdminDeleteReviewView,
    AdminPaymentListView,
    AdminCategoryListView,
    AdminDeleteCategoryView,
    AdminTagListView,
    AdminDeleteTagView,
)
 
urlpatterns = [
    # Dashboard
    path('dashboard/',                          AdminDashboardView.as_view(),           name='admin_dashboard'),
 
    # Users
    path('users/',                              AdminUserListView.as_view(),            name='admin_users'),
    path('users/<int:pk>/',                     AdminUserDetailView.as_view(),          name='admin_user_detail'),
    path('users/<int:pk>/toggle-active/',       AdminToggleUserActiveView.as_view(),    name='admin_toggle_user'),
    path('users/<int:pk>/delete/',              AdminDeleteUserView.as_view(),          name='admin_delete_user'),
 
    # Providers
    path('providers/',                          AdminProviderListView.as_view(),        name='admin_providers'),
    path('providers/<int:pk>/verify/',          AdminVerifyProviderView.as_view(),      name='admin_verify_provider'),
 
    # Courses
    path('courses/',                            AdminCourseListView.as_view(),          name='admin_courses'),
    path('courses/<int:pk>/toggle-publish/',    AdminToggleCoursePublishView.as_view(), name='admin_toggle_publish'),
    path('courses/<int:pk>/delete/',            AdminDeleteCourseView.as_view(),        name='admin_delete_course'),
 
    # Reviews
    path('reviews/',                            AdminReviewListView.as_view(),          name='admin_reviews'),
    path('reviews/<int:pk>/approve/',           AdminApproveReviewView.as_view(),       name='admin_approve_review'),
    path('reviews/<int:pk>/delete/',            AdminDeleteReviewView.as_view(),        name='admin_delete_review'),
 
    # Payments
    path('payments/',                           AdminPaymentListView.as_view(),         name='admin_payments'),
 
    # Categories
    path('categories/',                         AdminCategoryListView.as_view(),        name='admin_categories'),
    path('categories/<int:pk>/delete/',         AdminDeleteCategoryView.as_view(),      name='admin_delete_category'),
 
    # Tags
    path('tags/',                               AdminTagListView.as_view(),             name='admin_tags'),
    path('tags/<int:pk>/delete/',               AdminDeleteTagView.as_view(),           name='admin_delete_tag'),
]