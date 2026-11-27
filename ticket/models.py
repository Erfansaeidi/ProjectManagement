import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from .storage import private_ticket_storage
from .validators import ALLOWED_ATTACHMENT_EXTENSIONS, validate_ticket_attachment


def default_ticket_expiration():
    return timezone.now() + timedelta(days=30)


def _generate_private_upload_path(folder: str, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        ext = '.bin'
    return f'{folder}/{uuid.uuid4().hex}{ext}'


def ticket_attachment_upload_path(instance: 'Ticket', filename: str) -> str:
    return _generate_private_upload_path('tickets', filename)


def message_attachment_upload_path(instance: 'TicketMessage', filename: str) -> str:
    return _generate_private_upload_path('ticket_messages', filename)


class TicketQuerySet(models.QuerySet):
    def close_expired(self) -> int:
        now = timezone.now()
        return self.filter(
            expire_at__lte=now,
        ).exclude(
            status=Ticket.Status.CLOSED,
        ).update(
            status=Ticket.Status.CLOSED,
            updated_at=now,
        )

    def visible_to(self, user):
        self.close_expired()
        if user.is_staff:
            return self.all()
        return self.filter(user=user)


class TicketManager(models.Manager):
    def get_queryset(self) -> TicketQuerySet:
        return TicketQuerySet(self.model, using=self._db)

    def close_expired(self) -> int:
        return self.get_queryset().close_expired()

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


class Ticket(models.Model):
    class Category(models.TextChoices):
        TECHNICAL = 'technical', 'Technical'
        BILLING = 'billing', 'Billing'
        ACCOUNT = 'account', 'Account'
        GENERAL = 'general', 'General'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        CLOSED = 'closed', 'Closed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True},
        related_name='assigned_tickets',
    )
    subject = models.CharField(max_length=255)
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_at = models.DateTimeField(default=default_ticket_expiration)
    file = models.FileField(
        storage=private_ticket_storage,
        upload_to=ticket_attachment_upload_path,
        blank=True,
        null=True,
        validators=[validate_ticket_attachment],
    )

    objects = TicketManager()

    class Meta:
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'expire_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self) -> str:
        return f'#{self.pk} - {self.subject}'

    @property
    def is_expired(self) -> bool:
        return self.expire_at <= timezone.now()

    def sync_expiration(self) -> bool:
        if self.status != self.Status.CLOSED and self.is_expired:
            self.status = self.Status.CLOSED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_messages',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        storage=private_ticket_storage,
        upload_to=message_attachment_upload_path,
        blank=True,
        null=True,
        validators=[validate_ticket_attachment],
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'Message #{self.pk} on Ticket #{self.ticket_id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Ticket.objects.filter(pk=self.ticket_id).update(updated_at=timezone.now())