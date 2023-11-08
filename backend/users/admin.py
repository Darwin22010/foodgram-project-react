from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@register(User)
class MyUserAdmin(UserAdmin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name',
                    'password')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')


class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user__username", "author__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')


admin.site.register(Follow, FollowAdmin)
