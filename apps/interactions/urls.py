from django.urls import path
from .views import (
    StudentDashboardView,
    EnrollCourseView,
    UnenrollCourseView,
    MyEnrollmentsView,
    UpdateProgressView,
    WishlistView,
    WishlistAddView,
    WishlistRemoveView,
    WriteReviewView,
    DeleteReviewView,
)
 
urlpatterns = [
    # Student dashboard
    path('student/dashboard/',                          StudentDashboardView.as_view(),  name='student_dashboard'),
 
    # Enrollments
    path('enrollments/',                                MyEnrollmentsView.as_view(),     name='my_enrollments'),
    path('enroll/<int:course_id>/',                     EnrollCourseView.as_view(),      name='enroll'),
    path('unenroll/<int:course_id>/',                   UnenrollCourseView.as_view(),    name='unenroll'),
    path('enroll/<int:course_id>/progress/',            UpdateProgressView.as_view(),    name='update_progress'),
 
    # Wishlist
    path('wishlist/',                                   WishlistView.as_view(),          name='wishlist'),
    path('wishlist/add/<int:course_id>/',               WishlistAddView.as_view(),       name='wishlist_add'),
    path('wishlist/remove/<int:course_id>/',            WishlistRemoveView.as_view(),    name='wishlist_remove'),
 
    # Reviews
    path('courses/<int:course_id>/review/',             WriteReviewView.as_view(),       name='write_review'),
    path('reviews/<int:pk>/delete/',                    DeleteReviewView.as_view(),      name='delete_review'),
]
