import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Ticket, TicketMessage

User = get_user_model()
TEMP_PRIVATE_MEDIA = tempfile.mkdtemp()


@override_settings(PRIVATE_MEDIA_ROOT=TEMP_PRIVATE_MEDIA)
class TicketSystemTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_PRIVATE_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='Password123!')
        self.staff = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='Password123!',
            is_staff=True,
        )

        # Rebind storage location to test temporary directory
        Ticket._meta.get_field('file').storage.location = TEMP_PRIVATE_MEDIA
        TicketMessage._meta.get_field('file').storage.location = TEMP_PRIVATE_MEDIA

    def test_regular_user_ticket_creation_and_field_visibility(self):
        self.client.force_login(self.user1)
        pdf_file = SimpleUploadedFile('report.pdf', b'%PDF-1.4\n%fake-pdf-body', content_type='application/pdf')

        response = self.client.post(
            reverse('api_ticket_list_create'),
            data={
                'subject': 'Cannot access billing page',
                'category': Ticket.Category.BILLING,
                'file': pdf_file,
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()

        # Regular users only receive subject, category, status (and id)
        self.assertEqual(set(payload.keys()), {'id', 'subject', 'category', 'status'})
        self.assertNotIn('priority', payload)
        self.assertNotIn('expire_at', payload)

        ticket = Ticket.objects.get(pk=payload['id'])
        self.assertTrue(ticket.file.name.startswith('tickets/'))
        self.assertNotIn('report.pdf', ticket.file.name)

    def test_idor_protection_on_tickets_messages_and_files(self):
        pdf_file = SimpleUploadedFile('secret.pdf', b'%PDF-1.4\nsecret', content_type='application/pdf')
        ticket = Ticket.objects.create(
            user=self.user1,
            subject='Private Issue',
            category=Ticket.Category.ACCOUNT,
            file=pdf_file,
        )
        msg = TicketMessage.objects.create(ticket=ticket, sender=self.user1, body='Sensitive details')

        # Another regular user cannot access ticket detail, messages, or file download
        self.client.force_login(self.user2)
        self.assertEqual(self.client.get(reverse('ticket:ticket_detail', args=[ticket.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('ticket:ticket_attachment', args=[ticket.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('api_ticket_detail', args=[ticket.pk])).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse('api_ticket_messages', args=[ticket.pk]),
                data={'body': 'Hijack'},
            ).status_code,
            403,
        )

        # Owner and staff can download private attachment
        self.client.force_login(self.user1)
        owner_dl = self.client.get(reverse('ticket:ticket_attachment', args=[ticket.pk]))
        self.assertEqual(owner_dl.status_code, 200)
        self.assertEqual(owner_dl['X-Content-Type-Options'], 'nosniff')
        owner_dl.close()

        self.client.force_login(self.staff)
        staff_dl = self.client.get(reverse('ticket:ticket_attachment', args=[ticket.pk]))
        self.assertEqual(staff_dl.status_code, 200)
        staff_dl.close()

    def test_dangerous_or_spoofed_file_upload_rejected(self):
        self.client.force_login(self.user1)
        fake_pdf = SimpleUploadedFile('shell.pdf', b'#!/bin/bash\nrm -rf /', content_type='application/pdf')
        response = self.client.post(
            reverse('ticket:ticket_create'),
            data={
                'subject': 'Malicious upload',
                'category': Ticket.Category.TECHNICAL,
                'file': fake_pdf,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_staff_operations_and_automatic_expiration(self):
        ticket = Ticket.objects.create(user=self.user1, subject='Server Latency')

        # Regular user cannot close ticket
        self.client.force_login(self.user1)
        self.assertEqual(self.client.patch(reverse('api_ticket_close', args=[ticket.pk])).status_code, 403)

        # Staff can assign and change priority
        self.client.force_login(self.staff)
        assign_resp = self.client.post(
            reverse('api_staff_ticket_assign', args=[ticket.pk]),
            data={'staff_user_id': self.staff.pk},
        )
        self.assertEqual(assign_resp.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.assigned_to, self.staff)

        patch_resp = self.client.patch(
            reverse('api_staff_ticket_update', args=[ticket.pk]),
            data={'priority': Ticket.Priority.URGENT},
            content_type='application/json',
        )
        self.assertEqual(patch_resp.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.priority, Ticket.Priority.URGENT)

        # Expired ticket automatically closes
        Ticket.objects.filter(pk=ticket.pk).update(expire_at=timezone.now() - timedelta(minutes=1))
        Ticket.objects.close_expired()
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.CLOSED)