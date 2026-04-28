from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AccessRequest

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'status_badge', 'access_expires', 'is_staff', 'date_joined')
    list_filter = ('is_verified', 'is_blocked', 'is_staff', 'access_expires')
    actions = ['verify_users', 'block_users', 'unblock_users']

    def status_badge(self, obj):
        if obj.is_blocked:
            return format_html('<span class="badge-status badge-blocked">Blocked</span>')
        if obj.is_verified:
            return format_html('<span class="badge-status badge-verified">Verified</span>')
        return format_html('<span class="badge-status badge-pending">Pending Verification</span>')
    status_badge.short_description = "Account Status"

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Platform Access Control', {
            'fields': ('is_verified', 'is_blocked', 'access_expires'),
            'description': 'Control user verification, blocking status, and access expiration here.'
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
    verify_users.short_description = "Verify selected users"

    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)
    block_users.short_description = "Block selected users"

    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
    unblock_users.short_description = "Unblock selected users"

from django.utils.html import format_html

@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status_badge', 'view_proof_link', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'view_proof_full')

    def status_badge(self, obj):
        if obj.status == 'approved':
            return format_html('<span class="badge-status badge-verified">Approved</span>')
        if obj.status == 'declined':
            return format_html('<span class="badge-status badge-blocked">Declined</span>')
        return format_html('<span class="badge-status badge-pending">Waiting Approval</span>')
    status_badge.short_description = "Request Status"

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }
    
    fieldsets = (
        ('Applicant Details', {
            'fields': ('name', 'email', 'phone', 'whatsapp')
        }),
        ('Verification Proof', {
            'fields': ('proof', 'view_proof_full'),
            'description': 'Review the uploaded document before approving.'
        }),
        ('Decision', {
            'fields': ('status', 'created_at'),
        }),
    )
    
    actions = ['approve_requests', 'decline_requests']

    def view_proof_link(self, obj):
        if obj.proof:
            return format_html('<a href="{}" target="_blank" class="view-proof-btn">Review File</a>', obj.proof.url)
        return "No File"
    view_proof_link.short_description = "Proof Link"

    def view_proof_full(self, obj):
        if obj.proof:
            return format_html('<a href="{}" target="_blank">Download/View Full Proof Document</a>', obj.proof.url)
        return "No proof uploaded"
    view_proof_full.short_description = "Proof Action"

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
    approve_requests.short_description = "Mark selected as Approved"

    def decline_requests(self, request, queryset):
        queryset.update(status='declined')
    decline_requests.short_description = "Mark selected as Declined"
