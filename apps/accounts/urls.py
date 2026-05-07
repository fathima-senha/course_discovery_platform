from django.urls import path
from .views import (
    LandingPageView,
    RegisterView,
    LoginView,
    LogoutView,
    DashboardRedirectView,
    StudentProfileView,
    ProviderProfileView,
    ChangePasswordView,
)

urlpatterns = [
    # Landing
    path('',                    LandingPageView.as_view(),      name='landing'),

    # Auth
    path('register/',           RegisterView.as_view(),         name='register'),
    path('login/',              LoginView.as_view(),            name='login'),
    path('logout/',             LogoutView.as_view(),           name='logout'),
    path('dashboard/',          DashboardRedirectView.as_view(),name='dashboard_redirect'),
    path('change-password/',    ChangePasswordView.as_view(),   name='change_password'),

    # Profiles
    path('student/profile/',    StudentProfileView.as_view(),   name='student_profile'),
    path('provider/profile/',   ProviderProfileView.as_view(),  name='provider_profile'),
]