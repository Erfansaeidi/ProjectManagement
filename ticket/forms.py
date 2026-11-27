from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from account.forms import BootstrapFormMixin
from .models import Ticket, TicketMessage

User = get_user_model()


class RegularUserTicketCreateForm(BootstrapFormMixin, forms.ModelForm):
    initial_message = forms.CharField(
        required=False,
        label='Description / Initial Message',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your issue in detail...'}),
    )

    class Meta:
        model = Ticket
        fields = ('subject', 'category', 'file')
        widgets = {
            'file': forms.FileInput(
                attrs={'accept': '.pdf,.png,.jpg,.jpeg,.webp,.txt,.csv,.doc,.docx'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class RegularUserTicketUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('subject', 'category', 'file')
        widgets = {
            'file': forms.FileInput(
                attrs={'accept': '.pdf,.png,.jpg,.jpeg,.webp,.txt,.csv,.doc,.docx'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class StaffTicketUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('subject', 'category', 'priority', 'status', 'expire_at', 'assigned_to', 'file')
        widgets = {
            'expire_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'file': forms.FileInput(
                attrs={'accept': '.pdf,.png,.jpg,.jpeg,.webp,.txt,.csv,.doc,.docx'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True).order_by('username')
        if self.instance and self.instance.expire_at:
            self.initial['expire_at'] = self.instance.expire_at.strftime('%Y-%m-%dT%H:%M')
        self._apply_bootstrap_classes()


class TicketMessageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ('body', 'file')
        labels = {
            'body': 'Message',
            'file': 'Attachment (Optional)',
        }
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your reply...'}),
            'file': forms.FileInput(
                attrs={'accept': '.pdf,.png,.jpg,.jpeg,.webp,.txt,.csv,.doc,.docx'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_body(self) -> str:
        body = self.cleaned_data['body'].strip()
        if not body:
            raise ValidationError('Message body cannot be empty.')
        return body