from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from .models import StudentProfile, ProviderProfile
from .forms import (
    RegisterForm,
    LoginForm,
    StudentProfileForm,
    ProviderProfileForm,
    ChangePasswordForm,
)

User = get_user_model()


class LandingPageView(View):
    """
    GET /
    Shows the landing page to everyone.
    If already logged in, redirect to their dashboard.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        return render(request, 'landing.html')


class RegisterView(View):
    """
    GET  /register/  — shows the registration form
    POST /register/  — handles form submission
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard_redirect')
        return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    """
    GET  /login/   — shows login form
    POST /login/   — handles login
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user     = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard_redirect')
            messages.error(request, 'Invalid email or password.')
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    """
    POST /logout/  — logs the user out and returns to landing page
    """
    def post(self, request):
        logout(request)
        messages.success(request, 'Logged out successfully.')
        return redirect('landing')


class DashboardRedirectView(View):
    """
    GET /dashboard/
    Reads the user role and redirects to the correct dashboard.
    student  → /student/dashboard/
    provider → /provider/dashboard/
    admin    → /admin-panel/dashboard/
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        role = request.user.role
        if role == 'student':
            return redirect('student_dashboard')
        elif role == 'provider':
            return redirect('provider_dashboard')
        elif role == 'admin':
            return redirect('admin_dashboard')
        return redirect('landing')


@method_decorator(login_required, name='dispatch')
class StudentProfileView(View):
    """
    GET  /student/profile/  — shows profile edit page
    POST /student/profile/  — saves profile changes
    """
    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        profile = request.user.student_profile
        form    = StudentProfileForm(instance=profile)
        return render(request, 'accounts/student_profile.html', {
            'form': form, 'profile': profile,
        })

    def post(self, request):
        if request.user.role != 'student':
            return redirect('landing')
        profile = request.user.student_profile
        form    = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
        return render(request, 'accounts/student_profile.html', {
            'form': form, 'profile': profile,
        })


@method_decorator(login_required, name='dispatch')
class ProviderProfileView(View):
    """
    GET  /provider/profile/  — shows provider profile edit page
    POST /provider/profile/  — saves changes
    """
    def get(self, request):
        if request.user.role != 'provider':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        profile = request.user.provider_profile
        form    = ProviderProfileForm(instance=profile)
        return render(request, 'accounts/provider_profile.html', {
            'form': form, 'profile': profile,
        })

    def post(self, request):
        if request.user.role != 'provider':
            return redirect('landing')
        profile = request.user.provider_profile
        form    = ProviderProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('provider_profile')
        return render(request, 'accounts/provider_profile.html', {
            'form': form, 'profile': profile,
        })


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    """
    GET  /change-password/  — shows change password form
    POST /change-password/  — saves new password
    """
    def get(self, request):
        form = ChangePasswordForm()
        return render(request, 'accounts/change_password.html', {'form': form})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            if not request.user.check_password(old_password):
                messages.error(request, 'Old password is incorrect.')
                return render(request, 'accounts/change_password.html', {'form': form})
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)  # keep user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('dashboard_redirect')
        return render(request, 'accounts/change_password.html', {'form': form})