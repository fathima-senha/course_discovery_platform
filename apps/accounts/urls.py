from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ChangePasswordView,
    StudentProfileView,
    PublicStudentProfileView,
    ProviderProfileView,
    PublicProviderProfileView,
)

urlpatterns = [
    # Auth
    path("register/",           RegisterView.as_view(),         name="register"),
    path("login/",              LoginView.as_view(),            name="login"),
    path("logout/",             LogoutView.as_view(),           name="logout"),
    path("token/refresh/",      TokenRefreshView.as_view(),     name="token_refresh"),
    path("change-password/",    ChangePasswordView.as_view(),   name="change_password"),

    # Student profile
    path("student/profile/",            StudentProfileView.as_view(),       name="student_profile"),
    path("student/<int:pk>/",           PublicStudentProfileView.as_view(), name="public_student_profile"),

    # Provider profile
    path("provider/profile/",           ProviderProfileView.as_view(),      name="provider_profile"),
    path("provider/<int:pk>/",          PublicProviderProfileView.as_view(),name="public_provider_profile"),
]