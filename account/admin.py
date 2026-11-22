from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser
from .forms import CustomUserChangeForm , CustomUserCreationForm

class CustomUserAdmin (UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = [
        "username",
        "email",
        "is_staff",
        "id",
    ]
    fieldsets = UserAdmin.fieldsets + ((None,{"fields":("age",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None,{"fields":("age",)}),)

admin.site.register(CustomUser , CustomUserAdmin)

# Register your models here.
