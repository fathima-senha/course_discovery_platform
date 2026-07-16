from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from .models import StudentProfile, ProviderProfile

from django.core.mail import send_mail
from django.http import HttpResponse
from .forms import (
    RegisterForm,
    LoginForm,
    StudentProfileForm,
    ProviderProfileForm,
    ChangePasswordForm,
)

User = get_user_model()

class TestEmailView(View):
        def get(self, request):
            send_mail(
                subject="Test Email",
                message="Hello! Your email configuration is working.",
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=["fsenha2004@gmail.com"],  
                fail_silently=False,
            )

            return HttpResponse("Email sent successfully!")
           


class LandingPageView(View):
    """
    GET /
    Shows the landing page to everyone.
    If already logged in, redirect to their dashboard.
    """
    def get(self, request):
        # if request.user.is_authenticated:
        #     return redirect('dashboard_redirect')
        return render(request, 'landing.html')


class RegisterView(View):
    """
    GET  /register/  — shows the registration form
    POST /register/  — handles form submission
    """
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        
        register_form = RegisterForm()
        login_form = LoginForm()
        
        return render(request, 'accounts/login.html', {
            'register_form': register_form,
            'login_form': login_form,
            'active_tab': 'register'
        })

    
    def post(self, request):
        print("POST DATA:", request.POST)

        register_form = RegisterForm(request.POST)
        login_form = LoginForm()

        print("FORM DATA:", register_form.data)

        valid = register_form.is_valid()

        print("FORM VALID:", valid)

        if not valid:
            print("ERRORS:", register_form.errors)

        if valid:
            user = register_form.save()
            login(request, user)
            return redirect('dashboard_redirect')

        return render(request, 'accounts/login.html', {
            'register_form': register_form,
            'login_form': login_form,
            'active_tab': 'register'
        })
    
    # def post(self, request):
    #     register_form = RegisterForm(request.POST)
    #     login_form = LoginForm()
    #     if register_form.is_valid():
    #         user = register_form.save()
    #         login(request, user)
    #         messages.success(request, 'Account created successfully!')
    #         return redirect('dashboard_redirect')
    #     return render(request, 'accounts/login.html', {
    #         'register_form': register_form,
    #         'login_form': login_form,
    #         'active_tab': 'register'
    #     })


class LoginView(View):
    """
    GET  /login/   — shows login form
    POST /login/   — handles login
    """
    def get(self, request):
        login_form = LoginForm()
        register_form = RegisterForm()
        # if request.user.is_authenticated:
        #     return redirect('dashboard_redirect')
        return render(request, 'accounts/login.html', {
            'login_form': login_form,
            'register_form': register_form,
            'active_tab': 'login'
        })

    def post(self, request):
        login_form = LoginForm(request.POST)
        register_form = RegisterForm()
        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            user     = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard_redirect')
            messages.error(request, 'Invalid email or password.')
        return render(request, 'accounts/login.html', {
            'login_form': login_form,
            'register_form': register_form,
            'active_tab': 'login'
        })


class LogoutView(View):
    """
    POST /logout/  — logs the user out and returns to landing page
    """
    def post(self, request):
        logout(request)
        messages.success(request, 'Logged out successfully.')
        return redirect('landing')


# class DashboardRedirectView(View):
#     """
#     GET /dashboard/
#     Reads the user role and redirects to the correct dashboard.
#     student  → /student/dashboard/
#     provider → /provider/dashboard/
#     admin    → /admin-panel/dashboard/
#     """
#     def get(self, request):
#         print(request.user.role)
#         if not request.user.is_authenticated:
#             return redirect('login')
#         role = request.user.role
#         if role == 'student':
#             return redirect('student_dashboard')
#         elif role == 'provider':
#             return redirect('provider_dashboard')
#         elif role == 'admin':
#             return redirect('admin_dashboard')
#         return redirect('landing')

class DashboardRedirectView(View):

    def get(self, request):

        print(request.user.role)

        if not request.user.is_authenticated:
            return redirect('login')

        role = request.user.role

        if role == 'student':
            return redirect('student_profile')

        elif role == 'provider':
            return redirect('provider_profile')

        elif role == 'admin':
            return redirect('admin_dashboard')

        return redirect('landing')

class StudentProfileView(LoginRequiredMixin, View):
    """
    Handles viewing and updating the student's profile.

    GET  : Displays the profile edit form pre-filled with the student's
           existing information (bio, avatar, location, website, etc.).

    POST : Validates and saves the submitted profile information.
           If validation succeeds, the user is redirected back to the
           profile page with a success message. Otherwise, the form is
           re-rendered with validation errors.
    """

    template_name = "accounts/student_profile.html"

    def get(self, request):
        # Ensure only students can access this page
        if request.user.role != User.Role.STUDENT:
            messages.error(request, "Access denied.")
            return redirect("landing")

        # Fetch the logged-in student's profile
        profile = request.user.student_profile

        # Create a form pre-filled with existing profile data
        form = StudentProfileForm(instance=profile)

        return render(request, self.template_name, {
            "form": form,
            "profile": profile,
        })

    def post(self, request):
        # Ensure only students can update their profile
        if request.user.role != User.Role.STUDENT:
            messages.error(request, "Access denied.")
            return redirect("landing")

        # Fetch the student's profile
        profile = request.user.student_profile

        # Bind submitted data and uploaded files to the form
        form = StudentProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        # Validate and save the profile
        if form.is_valid():
            form.save()

            request.user.username = request.POST.get("username")
            request.user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("student_profile")

        # If validation fails, show the form again with errors
        messages.error(request, "Please correct the highlighted errors.")

        return render(request, self.template_name, {
            "form": form,
            "profile": profile,
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
    GET  /change-password/  — Show change password form
    POST /change-password/ — Change user's password
    """

    def get(self, request):
        form = ChangePasswordForm()
        return render(request, 'accounts/change_password.html', {
            'form': form
        })

    def post(self, request):
        form = ChangePasswordForm(request.POST)

        if not form.is_valid():
            return render(request, 'accounts/change_password.html', {
                'form': form
            })

        old_password = form.cleaned_data['old_password']
        new_password = form.cleaned_data['new_password']

        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
            return render(request, 'accounts/change_password.html', {
                'form': form
            })

        request.user.set_password(new_password)
        request.user.save()

        # Keep the user logged in after changing the password
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Password changed successfully!')
        return redirect('dashboard_redirect')
    
    
           