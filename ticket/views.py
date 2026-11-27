from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from .forms import (
    RegularUserTicketCreateForm,
    RegularUserTicketUpdateForm,
    StaffTicketUpdateForm,
    TicketMessageForm,
)
from .mixins import SupportStaffRequiredMixin, TicketAccessMixin
from .models import Ticket, TicketMessage


def _build_secure_attachment_response(file_field, download_prefix: str) -> FileResponse:
    if not file_field or not file_field.name:
        raise Http404('Attachment not found.')

    storage = file_field.storage
    if not storage.exists(file_field.name):
        raise Http404('Attachment file is missing from storage.')

    ext = Path(file_field.name).suffix.lower()
    safe_download_name = get_valid_filename(f'{download_prefix}{ext}')

    file_handle = storage.open(file_field.name, 'rb')
    response = FileResponse(file_handle, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{safe_download_name}"'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'ticket/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_queryset(self):
        Ticket.objects.close_expired()
        return Ticket.objects.filter(user=self.request.user).order_by('-updated_at')


class StaffTicketListView(SupportStaffRequiredMixin, ListView):
    model = Ticket
    template_name = 'ticket/staff_ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        Ticket.objects.close_expired()
        qs = Ticket.objects.select_related('user', 'assigned_to').all()
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        if status in Ticket.Status.values:
            qs = qs.filter(status=status)
        if priority in Ticket.Priority.values:
            qs = qs.filter(priority=priority)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Ticket.Status.choices
        context['priority_choices'] = Ticket.Priority.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_priority'] = self.request.GET.get('priority', '')
        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = RegularUserTicketCreateForm
    template_name = 'ticket/ticket_form.html'

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()

        initial_message = form.cleaned_data.get('initial_message', '').strip()
        if initial_message:
            TicketMessage.objects.create(
                ticket=self.object,
                sender=self.request.user,
                body=initial_message,
            )

        messages.success(self.request, 'Support ticket created successfully.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('ticket:ticket_detail', kwargs={'pk': self.object.pk})


class TicketDetailView(TicketAccessMixin, DetailView):
    model = Ticket
    template_name = 'ticket/ticket_detail.html'
    context_object_name = 'ticket'

    def get_object(self, queryset=None) -> Ticket:
        return self.get_authorized_ticket()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conversation'] = (
            self.object.messages.select_related('sender', 'sender__profile')
            .all()
            .order_by('created_at')
        )
        context['message_form'] = TicketMessageForm()
        context['is_staff_viewer'] = self.request.user.is_staff
        return context


class TicketMessageCreateView(TicketAccessMixin, FormView):
    form_class = TicketMessageForm

    def get(self, request, *args, **kwargs):
        return redirect('ticket:ticket_detail', pk=self.kwargs['pk'])

    def form_valid(self, form):
        ticket = self.get_authorized_ticket()
        if ticket.status == Ticket.Status.CLOSED:
            messages.error(self.request, 'Cannot send messages to a closed ticket.')
            return redirect('ticket:ticket_detail', pk=ticket.pk)

        message = form.save(commit=False)
        message.ticket = ticket
        message.sender = self.request.user
        message.save()

        messages.success(self.request, 'Reply sent.')
        return redirect('ticket:ticket_detail', pk=ticket.pk)

    def form_invalid(self, form):
        for errors in form.errors.values():
            for err in errors:
                messages.error(self.request, err)
        return redirect('ticket:ticket_detail', pk=self.kwargs['pk'])


class TicketUpdateView(TicketAccessMixin, UpdateView):
    model = Ticket
    template_name = 'ticket/ticket_form.html'

    def get_object(self, queryset=None) -> Ticket:
        ticket = self.get_authorized_ticket()
        if not self.request.user.is_staff and ticket.status == Ticket.Status.CLOSED:
            raise PermissionDenied('Closed tickets cannot be edited by regular users.')
        return ticket

    def get_form_class(self):
        if self.request.user.is_staff:
            return StaffTicketUpdateForm
        return RegularUserTicketUpdateForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Ticket updated successfully.')
        return response

    def get_success_url(self):
        return reverse('ticket:ticket_detail', kwargs={'pk': self.object.pk})


class TicketCloseView(SupportStaffRequiredMixin, View):
    def post(self, request, pk: int, *args, **kwargs):
        Ticket.objects.close_expired()
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.status != Ticket.Status.CLOSED:
            ticket.status = Ticket.Status.CLOSED
            ticket.updated_at = timezone.now()
            ticket.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Ticket #{ticket.pk} has been closed.')
        return redirect('ticket:ticket_detail', pk=ticket.pk)


class TicketAttachmentDownloadView(TicketAccessMixin, View):
    def get(self, request, pk: int, *args, **kwargs):
        ticket = self.get_authorized_ticket()
        return _build_secure_attachment_response(
            ticket.file,
            download_prefix=f'ticket_{ticket.pk}_attachment',
        )


class MessageAttachmentDownloadView(TicketAccessMixin, View):
    ticket_url_kwarg = 'ticket_pk'

    def get(self, request, ticket_pk: int, message_pk: int, *args, **kwargs):
        ticket = self.get_authorized_ticket()
        message = get_object_or_404(TicketMessage, pk=message_pk, ticket=ticket)
        return _build_secure_attachment_response(
            message.file,
            download_prefix=f'ticket_{ticket.pk}_message_{message.pk}',
        )