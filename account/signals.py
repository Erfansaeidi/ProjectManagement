from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created: bool, **kwargs) -> None:
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'role': Profile.Role.NONE},
        )