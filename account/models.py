import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.templatetags.static import static

from .validators import ALLOWED_EXTENSIONS, validate_profile_picture


def profile_picture_upload_path(instance: 'Profile', filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = '.png'
    return f'profile_pictures/{uuid.uuid4().hex}{ext}'


class WorkGroup(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_group',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @classmethod
    @transaction.atomic
    def create_with_owner(cls, *, name: str, description: str, owner) -> 'WorkGroup':
        owner_profile = Profile.objects.select_for_update().get(user=owner)
        if owner_profile.group_id is not None or hasattr(owner, 'owned_group'):
            raise ValidationError('User already belongs to or owns a group.')

        group = cls.objects.create(
            name=name,
            description=description,
            owner=owner,
        )
        owner_profile.group = group
        if owner_profile.role != Profile.Role.ADMIN:
            owner_profile.role = Profile.Role.MANAGER
        owner_profile.save(update_fields=['group', 'role', 'updated_at'])
        return group

    @transaction.atomic
    def add_member(self, user) -> 'Profile':
        target_profile = Profile.objects.select_for_update().get(user=user)
        if target_profile.group_id is not None or hasattr(user, 'owned_group'):
            raise ValidationError('This user already belongs to a group.')

        target_profile.group = self
        if target_profile.role != Profile.Role.ADMIN:
            target_profile.role = Profile.Role.MEMBER
        target_profile.save(update_fields=['group', 'role', 'updated_at'])
        return target_profile

    @transaction.atomic
    def remove_member(self, user) -> 'Profile':
        if user.id == self.owner_id:
            raise ValidationError('Group owner cannot be removed as a regular member.')

        target_profile = Profile.objects.select_for_update().get(user=user)
        if target_profile.group_id != self.id:
            raise ValidationError('User does not belong to this group.')

        target_profile.group = None
        if target_profile.role != Profile.Role.ADMIN:
            target_profile.role = Profile.Role.NONE
        target_profile.save(update_fields=['group', 'role', 'updated_at'])
        return target_profile

    @transaction.atomic
    def transfer_ownership(self, new_owner) -> None:
        if new_owner.id == self.owner_id:
            raise ValidationError('Selected user is already the group owner.')

        new_owner_profile = Profile.objects.select_for_update().get(user=new_owner)
        if new_owner_profile.group_id != self.id:
            raise ValidationError('New owner must be an existing member of this group.')

        old_owner_profile = Profile.objects.select_for_update().get(user=self.owner)

        self.owner = new_owner
        self.save(update_fields=['owner', 'updated_at'])

        if old_owner_profile.role != Profile.Role.ADMIN:
            old_owner_profile.role = Profile.Role.MEMBER
            old_owner_profile.save(update_fields=['role', 'updated_at'])

        if new_owner_profile.role != Profile.Role.ADMIN:
            new_owner_profile.role = Profile.Role.MANAGER
            new_owner_profile.save(update_fields=['role', 'updated_at'])

    @transaction.atomic
    def delete(self, *args, **kwargs):
        member_profiles = list(Profile.objects.select_for_update().filter(group=self))
        for profile in member_profiles:
            profile.group = None
            if profile.role != Profile.Role.ADMIN:
                profile.role = Profile.Role.NONE
            profile.save(update_fields=['group', 'role', 'updated_at'])
        return super().delete(*args, **kwargs)


class Profile(models.Model):
    class Role(models.TextChoices):
        NONE = 'none', 'None'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        MANAGER = 'manager', 'Manager'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    group = models.ForeignKey(
        WorkGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.NONE,
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path,
        blank=True,
        null=True,
        validators=[validate_profile_picture],
    )
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self) -> str:
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def get_profile_picture_url(self) -> str:
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return static('account/img/default-avatar.svg')

    def remove_profile_picture(self) -> None:
        if self.profile_picture:
            old_picture = self.profile_picture
            self.profile_picture = None
            self.save(update_fields=['profile_picture', 'updated_at'])
            old_picture.delete(save=False)