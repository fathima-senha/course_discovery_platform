from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile, ProviderProfile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == User.Role.STUDENT:
        StudentProfile.objects.create(user=instance)

    elif instance.role == User.Role.PROVIDER:
        ProviderProfile.objects.create(user=instance)