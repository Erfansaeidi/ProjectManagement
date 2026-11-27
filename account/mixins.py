from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Profile, WorkGroup


class UserProfileMixin(LoginRequiredMixin):
    def get_user_profile(self) -> Profile:
        profile, _ = Profile.objects.select_related('group', 'user').get_or_create(
            user=self.request.user
        )
        return profile


class GroupMemberRequiredMixin(UserProfileMixin):
    def get_user_group(self) -> WorkGroup:
        profile = self.get_user_profile()
        if profile.group is None:
            raise PermissionDenied('You do not belong to any group.')
        return profile.group


class GroupManagerRequiredMixin(GroupMemberRequiredMixin):
    def get_managed_group(self) -> WorkGroup:
        group = self.get_user_group()
        profile = self.get_user_profile()
        is_valid_manager = (
            group.owner_id == self.request.user.id
            and profile.role in (Profile.Role.MANAGER, Profile.Role.ADMIN)
        )
        if not is_valid_manager:
            raise PermissionDenied('Only the group manager can perform this action.')
        return group


class SameGroupProfileAccessMixin(UserProfileMixin):
    def get_authorized_target_profile(self) -> Profile:
        target_profile = get_object_or_404(
            Profile.objects.select_related('user', 'group'),
            user_id=self.kwargs['user_id'],
        )
        viewer_profile = self.get_user_profile()

        if target_profile.user_id == self.request.user.id:
            return target_profile

        if (
            viewer_profile.group_id is not None
            and viewer_profile.group_id == target_profile.group_id
        ):
            return target_profile

        raise PermissionDenied('You are not authorized to view profiles outside your group.')