from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow

User = get_user_model()


class CustomUserAdmin(BaseUserAdmin):
    list_display = ("email", "username",)
    list_filter = ("email", "username")


admin.site.register(User, CustomUserAdmin)


class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user__username", "author__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')


admin.site.register(Follow, FollowAdmin)
