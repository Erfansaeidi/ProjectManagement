import json
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View

from .models import Ticket, TicketMessage

User = get_user_model()


def _parse_request_payload(request) -> dict:
    content_type = request.content_type or ''
    if 'application/json' in content_type:
        if not request.body:
            return {}
        try:
            data = json.loads(request.body.decode('utf-8'))
            if not isinstance(data, dict):
                raise ValueError('JSON body must be an object.')
            return data
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValidationError('Invalid JSON payload.') from exc
    return request.POST.dict()


def _serialize_ticket(ticket: Ticket, *, is_staff: bool) -> dict:
    # Regular users can only view subject, category, and status
    base_data = {
        'id': ticket.pk,
        'subject': ticket.subject,
        'category': ticket.category,
        'status': ticket.status,
    }
    if not is_staff:
        return base_data

    return {
        **base_data,
        'user_id': ticket.user_id,
        'username': ticket.user.username,
        'assigned_to': ticket.assigned_to_id,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat(),
        'updated_at': ticket.updated_at.isoformat(),
        'expire_at': ticket.expire_at.isoformat(),
        'has_file': bool(ticket.file),
    }


def _serialize_message(message: TicketMessage) -> dict:
    return {
        'id': message.pk,
        'ticket_id': message.ticket_id,
        'sender_id': message.sender_id,
        'sender_username': message.sender.username,
        'is_staff_sender': message.sender.is_staff,
        'body': message.body,
        'created_at': message.created_at.isoformat(),
        'has_file': bool(message.file),
    }


class ApiAuthMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
        return super().dispatch(request, *args, **kwargs)


class ApiStaffRequiredMixin(ApiAuthMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
        if not request.user.is_staff:
            return JsonResponse({'detail': 'Support staff privileges are required.'}, status=403)
        return super().dispatch(request, *args, **kwargs)


class ApiTicketListCreateView(ApiAuthMixin, View):
    def get(self, request, *args, **kwargs):
        Ticket.objects.close_expired()
        tickets = Ticket.objects.filter(user=request.user).order_by('-updated_at')
        data = [_serialize_ticket(t, is_staff=request.user.is_staff) for t in tickets]
        return JsonResponse({'tickets': data}, status=200)

    def post(self, request, *args, **kwargs):
        try:
            payload = _parse_request_payload(request)
        except ValidationError as exc:
            return JsonResponse({'detail': exc.message}, status=400)

        subject = str(payload.get('subject', '')).strip()
        category = str(payload.get('category', Ticket.Category.GENERAL)).strip()
        uploaded_file = request.FILES.get('file')

        if not subject:
            return JsonResponse({'detail': 'Field "subject" is required.'}, status=400)
        if category not in Ticket.Category.values:
            return JsonResponse({'detail': 'Invalid category value.'}, status=400)

        ticket = Ticket(
            user=request.user,
            subject=subject,
            category=category,
            file=uploaded_file,
        )
        try:
            ticket.full_clean()
            ticket.save()
        except ValidationError as exc:
            return JsonResponse({'errors': exc.message_dict}, status=400)

        return JsonResponse(_serialize_ticket(ticket, is_staff=request.user.is_staff), status=201)


class ApiTicketDetailView(ApiAuthMixin, View):
    def get(self, request, pk: int, *args, **kwargs):
        Ticket.objects.close_expired()
        ticket = get_object_or_404(Ticket.objects.select_related('user'), pk=pk)
        if not request.user.is_staff and ticket.user_id != request.user.id:
            return JsonResponse({'detail': 'Not authorized to access this ticket.'}, status=403)

        return JsonResponse(_serialize_ticket(ticket, is_staff=request.user.is_staff), status=200)


class ApiTicketMessageListCreateView(ApiAuthMixin, View):
    def _get_ticket_or_forbidden(self, request, pk: int):
        Ticket.objects.close_expired()
        ticket = get_object_or_404(Ticket, pk=pk)
        if not request.user.is_staff and ticket.user_id != request.user.id:
            return None
        return ticket

    def get(self, request, pk: int, *args, **kwargs):
        ticket = self._get_ticket_or_forbidden(request, pk)
        if ticket is None:
            return JsonResponse({'detail': 'Not authorized to view messages for this ticket.'}, status=403)

        qs = ticket.messages.select_related('sender').order_by('created_at')
        return JsonResponse({'messages': [_serialize_message(m) for m in qs]}, status=200)

    def post(self, request, pk: int, *args, **kwargs):
        ticket = self._get_ticket_or_forbidden(request, pk)
        if ticket is None:
            return JsonResponse({'detail': 'Not authorized to reply to this ticket.'}, status=403)

        if ticket.status == Ticket.Status.CLOSED:
            return JsonResponse({'detail': 'Cannot post messages to a closed ticket.'}, status=400)

        try:
            payload = _parse_request_payload(request)
        except ValidationError as exc:
            return JsonResponse({'detail': exc.message}, status=400)

        body = str(payload.get('body', '')).strip()
        uploaded_file = request.FILES.get('file')
        if not body:
            return JsonResponse({'detail': 'Field "body" is required.'}, status=400)

        message = TicketMessage(
            ticket=ticket,
            sender=request.user,
            body=body,
            file=uploaded_file,
        )
        try:
            message.full_clean()
            message.save()
        except ValidationError as exc:
            return JsonResponse({'errors': exc.message_dict}, status=400)

        return JsonResponse(_serialize_message(message), status=201)


class ApiStaffTicketListView(ApiStaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        Ticket.objects.close_expired()
        tickets = Ticket.objects.select_related('user').all()
        return JsonResponse({'tickets': [_serialize_ticket(t, is_staff=True) for t in tickets]}, status=200)


class ApiStaffTicketUpdateView(ApiStaffRequiredMixin, View):
    def patch(self, request, pk: int, *args, **kwargs):
        Ticket.objects.close_expired()
        ticket = get_object_or_404(Ticket.objects.select_related('user'), pk=pk)

        try:
            payload = _parse_request_payload(request)
        except ValidationError as exc:
            return JsonResponse({'detail': exc.message}, status=400)

        if 'priority' in payload:
            if payload['priority'] not in Ticket.Priority.values:
                return JsonResponse({'detail': 'Invalid priority value.'}, status=400)
            ticket.priority = payload['priority']

        if 'status' in payload:
            if payload['status'] not in Ticket.Status.values:
                return JsonResponse({'detail': 'Invalid status value.'}, status=400)
            ticket.status = payload['status']

        if 'expire_at' in payload:
            parsed_dt = parse_datetime(str(payload['expire_at']))
            if parsed_dt is None:
                return JsonResponse({'detail': 'Invalid ISO datetime for expire_at.'}, status=400)
            if timezone.is_naive(parsed_dt):
                parsed_dt = timezone.make_aware(parsed_dt, timezone.get_current_timezone())
            ticket.expire_at = parsed_dt

        ticket.save()
        return JsonResponse(_serialize_ticket(ticket, is_staff=True), status=200)


class ApiStaffTicketCloseView(ApiStaffRequiredMixin, View):
    def patch(self, request, pk: int, *args, **kwargs):
        ticket = get_object_or_404(Ticket.objects.select_related('user'), pk=pk)
        ticket.status = Ticket.Status.CLOSED
        ticket.save(update_fields=['status', 'updated_at'])
        return JsonResponse(_serialize_ticket(ticket, is_staff=True), status=200)


class ApiStaffTicketAssignView(ApiStaffRequiredMixin, View):
    def post(self, request, pk: int, *args, **kwargs):
        ticket = get_object_or_404(Ticket.objects.select_related('user'), pk=pk)
        try:
            payload = _parse_request_payload(request)
        except ValidationError as exc:
            return JsonResponse({'detail': exc.message}, status=400)

        staff_user_id = payload.get('staff_user_id')
        if staff_user_id is None:
            assignee = request.user
        else:
            assignee = get_object_or_404(User, pk=staff_user_id, is_staff=True)

        ticket.assigned_to = assignee
        if ticket.status == Ticket.Status.OPEN:
            ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save(update_fields=['assigned_to', 'status', 'updated_at'])
        return JsonResponse(_serialize_ticket(ticket, is_staff=True), status=200)