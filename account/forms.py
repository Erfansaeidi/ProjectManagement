from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Profile, WorkGroup

User = get_user_model()


class BootstrapFormMixin:
    def _apply_bootstrap_classes(self) -> None:
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_email(self) -> str:
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email


class ProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ('bio', 'profile_picture')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        self._apply_bootstrap_classes()

    def clean_email(self) -> str:
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('This email is already in use by another account.')
        return email

    def save(self, commit: bool = True) -> Profile:
        old_picture = None
        if self.instance.pk and 'profile_picture' in self.changed_data:
            previous = Profile.objects.get(pk=self.instance.pk)
            if previous.profile_picture:
                old_picture = previous.profile_picture

        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = self.cleaned_data['email']

        if commit:
            user.save(update_fields=['first_name', 'last_name', 'email'])
            profile.save()
            if old_picture and old_picture != profile.profile_picture:
                old_picture.delete(save=False)

        return profile


class WorkGroupForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = WorkGroup
        fields = ('name', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class AddGroupMemberForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Username',
        help_text='Enter the exact username of a user who does not belong to any group.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        try:
            user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist as exc:
            raise ValidationError('No user found with this username.') from exc

        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.group_id is not None or hasattr(user, 'owned_group'):
            raise ValidationError('This user already belongs to or owns a group.')

        return user