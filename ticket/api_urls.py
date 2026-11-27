from django.urls import path

from .api_views import (
    ApiStaffTicketAssignView,
    ApiStaffTicketCloseView,
    ApiStaffTicketListView,
    ApiStaffTicketUpdateView,
    ApiTicketDetailView,
    ApiTicketListCreateView,
    ApiTicketMessageListCreateView,
)

urlpatterns = [
    path('tickets/', ApiTicketListCreateView.as_view(), name='api_ticket_list_create'),
    path('tickets/<int:pk>/', ApiTicketDetailView.as_view(), name='api_ticket_detail'),
    path('tickets/<int:pk>/messages/', ApiTicketMessageListCreateView.as_view(), name='api_ticket_messages'),
    path('tickets/<int:pk>/close/', ApiStaffTicketCloseView.as_view(), name='api_ticket_close'),
    path('staff/tickets/', ApiStaffTicketListView.as_view(), name='api_staff_ticket_list'),
    path('staff/tickets/<int:pk>/', ApiStaffTicketUpdateView.as_view(), name='api_staff_ticket_update'),
    path('staff/tickets/<int:pk>/assign/', ApiStaffTicketAssignView.as_view(), name='api_staff_ticket_assign'),
]