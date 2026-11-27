from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, TemplateView, UpdateView

from .forms import AddGroupMemberForm, ProfileUpdateForm, SignUpForm, WorkGroupForm
from .mixins import (
    GroupManagerRequiredMixin,
    GroupMemberRequiredMixin,
    SameGroupProfileAccessMixin,
    UserProfileMixin,
)
from .models import Profile, WorkGroup

User = get_user_model()


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile, _ = Profile.objects.select_related('group').get_or_create(
                user=self.request.user
            )
            context['profile'] = profile
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully. You can now log in.')
        return response


class MyProfileDetailView(UserProfileMixin, DetailView):
    model = Profile
    template_name = 'account/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None) -> Profile:
        return self.get_user_profile()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = True
        return context


class UserProfileDetailView(SameGroupProfileAccessMixin, DetailView):
    model = Profile
    template_name = 'account/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None) -> Profile:
        return self.get_authorized_target_profile()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = self.object.user_id == self.request.user.id
        return context


class ProfileUpdateView(UserProfileMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'account/profile_form.html'
    success_url = reverse_lazy('my_profile')

    def get_object(self, queryset=None) -> Profile:
        return self.get_user_profile()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully.')
        return response


class ProfilePictureDeleteView(UserProfileMixin, View):
    def post(self, request, *args, **kwargs):
        profile = self.get_user_profile()
        if profile.profile_picture:
            profile.remove_profile_picture()
            messages.success(request, 'Profile picture removed.')
        return redirect('profile_edit')


class WorkGroupCreateView(UserProfileMixin, CreateView):
    model = WorkGroup
    form_class = WorkGroupForm
    template_name = 'account/group_form.html'
    success_url = reverse_lazy('group_detail')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = self.get_user_profile()
            if profile.group_id is not None or hasattr(request.user, 'owned_group'):
                messages.warning(request, 'You already belong to a group.')
                return redirect('group_detail')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            self.object = WorkGroup.create_with_owner(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                owner=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Group created. Your role is now Manager.')
        return redirect(self.get_success_url())


class WorkGroupDetailView(GroupMemberRequiredMixin, DetailView):
    model = WorkGroup
    template_name = 'account/group_detail.html'
    context_object_name = 'group'

    def get_object(self, queryset=None) -> WorkGroup:
        return self.get_user_group()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_user_profile()
        is_manager = (
            self.object.owner_id == self.request.user.id
            and profile.role in (Profile.Role.MANAGER, Profile.Role.ADMIN)
        )
        context['is_manager'] = is_manager
        context['members'] = (
            Profile.objects.select_related('user')
            .filter(group=self.object)
            .order_by('user__username')
        )
        if is_manager:
            context['add_member_form'] = AddGroupMemberForm()
        return context


class WorkGroupUpdateView(GroupManagerRequiredMixin, UpdateView):
    model = WorkGroup
    form_class = WorkGroupForm
    template_name = 'account/group_form.html'
    success_url = reverse_lazy('group_detail')

    def get_object(self, queryset=None) -> WorkGroup:
        return self.get_managed_group()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Group details updated.')
        return response


class WorkGroupDeleteView(GroupManagerRequiredMixin, DeleteView):
    model = WorkGroup
    template_name = 'account/group_confirm_delete.html'
    success_url = reverse_lazy('home')
    context_object_name = 'group'

    def get_object(self, queryset=None) -> WorkGroup:
        return self.get_managed_group()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Group deleted and all members reset to None.')
        return response


class WorkGroupAddMemberView(GroupManagerRequiredMixin, FormView):
    form_class = AddGroupMemberForm
    success_url = reverse_lazy('group_detail')

    def http_method_not_allowed(self, request, *args, **kwargs):
        return redirect('group_detail')

    def get(self, request, *args, **kwargs):
        return redirect('group_detail')

    def form_valid(self, form):
        group = self.get_managed_group()
        target_user = form.cleaned_data['username']
        try:
            group.add_member(target_user)
            messages.success(
                self.request,
                f'{target_user.username} added to {group.name} as Member.',
            )
        except ValidationError as exc:
            messages.error(self.request, exc.message)
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        for errors in form.errors.values():
            for error in errors:
                messages.error(self.request, error)
        return redirect('group_detail')


class WorkGroupRemoveMemberView(GroupManagerRequiredMixin, View):
    def post(self, request, user_id: int, *args, **kwargs):
        group = self.get_managed_group()
        target_user = get_object_or_404(User, pk=user_id)
        try:
            group.remove_member(target_user)
            messages.success(request, f'{target_user.username} removed from {group.name}.')
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect('group_detail')


class WorkGroupLeaveView(GroupMemberRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        group = self.get_user_group()
        if group.owner_id == request.user.id:
            raise PermissionDenied('Group owner must transfer ownership or delete the group before leaving.')
        group.remove_member(request.user)
        messages.success(request, f'You have left {group.name}.')
        return redirect('home')


class WorkGroupTransferOwnershipView(GroupManagerRequiredMixin, View):
    def post(self, request, user_id: int, *args, **kwargs):
        group = self.get_managed_group()
        new_owner = get_object_or_404(User, pk=user_id)
        try:
            group.transfer_ownership(new_owner)
            messages.success(request, f'Group ownership transferred to {new_owner.username}.')
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect('group_detail')