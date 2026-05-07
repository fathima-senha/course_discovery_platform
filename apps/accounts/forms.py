from django import forms
from django.contrib.auth import get_user_model
from .models import StudentProfile, ProviderProfile

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """
    Registration form for both students and providers.
    Automatically creates the correct profile after saving.
    """
    password  = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model  = User
        fields = ['username', 'email', 'role', 'password', 'password2']

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == 'admin':
            raise forms.ValidationError('Cannot register as admin.')
        return role

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Auto-create the correct profile
            if user.role == 'student':
                StudentProfile.objects.create(user=user)
            elif user.role == 'provider':
                ProviderProfile.objects.create(
                    user=user,
                    company_name=user.username,
                )
        return user


class LoginForm(forms.Form):
    """Simple email + password login form."""
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class StudentProfileForm(forms.ModelForm):
    """Form for student to edit their profile."""
    class Meta:
        model  = StudentProfile
        fields = ['bio', 'avatar', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class ProviderProfileForm(forms.ModelForm):
    """Form for provider to edit their company profile."""
    class Meta:
        model  = ProviderProfile
        fields = ['company_name', 'website', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ChangePasswordForm(forms.Form):
    """Form for changing password."""
    old_password     = forms.CharField(widget=forms.PasswordInput)
    new_password     = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned_data