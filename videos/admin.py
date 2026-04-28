from django.contrib import admin
from .models import Category, Video, WatchHistory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title',)
    
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'youtube_url', 'category')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'watched_at')
    list_filter = ('watched_at', 'user')
    search_fields = ('user__username', 'video__title')
    readonly_fields = ('watched_at',)
