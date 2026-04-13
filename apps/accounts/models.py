from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    
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
    
    def is_admin(self):
        return self.role == self.Role.ADMIN