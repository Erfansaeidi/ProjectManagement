from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Ticket


class SupportStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return bool(self.request.user.is_authenticated and self.request.user.is_staff)


class TicketAccessMixin(LoginRequiredMixin):
    ticket_url_kwarg = 'pk'

    def get_authorized_ticket(self) -> Ticket:
        Ticket.objects.close_expired()
        ticket_id = self.kwargs[self.ticket_url_kwarg]
        ticket = get_object_or_404(
            Ticket.objects.select_related('user', 'user__profile', 'assigned_to'),
            pk=ticket_id,
        )
        if not self.request.user.is_staff and ticket.user_id != self.request.user.id:
            raise PermissionDenied('You do not have permission to access this ticket.')
        return ticket