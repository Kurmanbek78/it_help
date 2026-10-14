from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Comment, Ticket, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Роль", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Роль", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "author", "assignee", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("title", "description")


admin.site.register(Comment)