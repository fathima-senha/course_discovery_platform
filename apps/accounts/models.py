from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model with role-based access.
    Extends AbstractUser so Django's auth system works out of the box.
    """
    class Role(models.TextChoices):
        
        STUDENT = "student", _("Student")  
        PROVIDER = "provider", _("Provider")  
        ADMIN = "admin", _("Admin")
        
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT,)        
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "auth_user"
        verbose_name = "user"
        verbose_name_plural = "Users"
                
    def __str__(self):
        return f"{self.email}({self.role})"
            
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
            
    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    
class StudentProfile(models.Model):
    
    """
    One-to-one extension of User for students.
    Stores personal preferences and profile info.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/students/", blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class meta:
        db_table = "student_profile"
        verbose_name = "Student Profile"
        
    def __str__(self):
        return f"Student:{self.user.email}"
    
class ProviderProfile(models.Model):
    """
    One-to-one extension of User for course providers (institutes/companies).
    """
    
    user=models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="provider_profile",
        limit_choices_to={"role": User.Role.PROVIDER},
    )
    company_name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="logos/providers/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "provider_profile"
        verbose_name = "Provider Profile"
        
    def __str__(self):
        return self.company_name