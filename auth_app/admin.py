from django.contrib import admin

# Register your models here.
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'phone_number', 'country', 'is_online', 'is_active')
    list_filter = ('is_online', 'is_active', 'country')
    search_fields = ('username', 'email', 'full_name', 'phone_number')
    ordering = ('username',)
