from django.contrib import admin
from .models import (
    UserAccount, Scheme, UserDocument, Application,
    SchemeBookmark, SchemeFeedback, SchemeReport, ContactMessage, SchemeUpdate
)

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'role', 'occupation', 'state', 'created_at')
    list_filter = ('role', 'state', 'occupation', 'category')
    search_fields = ('full_name', 'email', 'phone', 'district')

@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'ministry', 'gov_level', 'state_coverage', 'status', 'ai_score', 'is_active')
    list_filter = ('category', 'gov_level', 'status', 'is_active')
    search_fields = ('name', 'ministry', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'doc_key', 'doc_type_name', 'category', 'status', 'uploaded_at')
    list_filter = ('status', 'category', 'doc_key')
    search_fields = ('user__email', 'user__full_name', 'file_name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'scheme_name', 'user', 'status', 'stage', 'submitted_date', 'last_updated')
    list_filter = ('status', 'stage')
    search_fields = ('application_id', 'scheme_name', 'user__email', 'user__full_name')

@admin.register(SchemeBookmark)
class SchemeBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'scheme', 'created_at')

@admin.register(SchemeFeedback)
class SchemeFeedbackAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'user', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(SchemeReport)
class SchemeReportAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'user', 'resolved', 'created_at')
    list_filter = ('resolved',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'subject')
    search_fields = ('name', 'email', 'message')

@admin.register(SchemeUpdate)
class SchemeUpdateAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'ministry_or_node', 'status', 'created_at')
    list_filter = ('status',)
