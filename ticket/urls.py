from django.urls import path

from .views import (
    MessageAttachmentDownloadView,
    StaffTicketListView,
    TicketAttachmentDownloadView,
    TicketCloseView,
    TicketCreateView,
    TicketDetailView,
    TicketListView,
    TicketMessageCreateView,
    TicketUpdateView,
)

app_name = 'ticket'

urlpatterns = [
    path('', TicketListView.as_view(), name='ticket_list'),
    path('new/', TicketCreateView.as_view(), name='ticket_create'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/edit/', TicketUpdateView.as_view(), name='ticket_update'),
    path('<int:pk>/messages/', TicketMessageCreateView.as_view(), name='message_create'),
    path('<int:pk>/attachment/', TicketAttachmentDownloadView.as_view(), name='ticket_attachment'),
    path(
        '<int:ticket_pk>/messages/<int:message_pk>/attachment/',
        MessageAttachmentDownloadView.as_view(),
        name='message_attachment',
    ),
    path('staff/', StaffTicketListView.as_view(), name='staff_ticket_list'),
    path('staff/<int:pk>/close/', TicketCloseView.as_view(), name='ticket_close'),
]