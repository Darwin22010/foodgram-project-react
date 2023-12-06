from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@admin.register(User)
class MyUserAdmin(UserAdmin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name',
                    'password')
    list_display_links = ["username", "email"]
    search_fields = ('first_name', 'last_name', 'username', 'email')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "id", "author")
    search_fields = ("user__username", "author__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')
