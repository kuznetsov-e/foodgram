from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import Subscription

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',)
    search_fields = ('username', 'email',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'first_name', 'last_name',)}),
        ('Права', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions',)}),
        ('Важные даты', {'fields': ('last_login', 'date_joined',)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_to',)
