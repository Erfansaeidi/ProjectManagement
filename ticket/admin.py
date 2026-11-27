from django.contrib import admin

from .models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ('sender', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'category', 'priority', 'status', 'assigned_to', 'expire_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('subject', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'sender', 'created_at')
    search_fields = ('body', 'sender__username', 'ticket__subject')
    readonly_fields = ('created_at',)