from django.contrib import admin

from .models import Profile, WorkGroup


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'group', 'updated_at')
    list_filter = ('role', 'group')
    search_fields = ('user__username', 'user__email', 'group__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly.append('role')
        return readonly


@admin.register(WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')