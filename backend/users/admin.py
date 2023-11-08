from django.contrib import admin

from .models import Follow


class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user__username", "author__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')


admin.site.register(Follow, FollowAdmin)
