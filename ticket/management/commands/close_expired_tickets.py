from django.core.management.base import BaseCommand

from ticket.models import Ticket


class Command(BaseCommand):
    help = 'Automatically closes all support tickets whose expiration timestamp has passed.'

    def handle(self, *args, **options) -> None:
        closed_count = Ticket.objects.close_expired()
        self.stdout.write(self.style.SUCCESS(f'Closed {closed_count} expired ticket(s).'))