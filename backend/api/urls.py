from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.login_view, name='login'),
    path('auth/signup/', views.signup_view, name='signup'),
    path('auth/register/', views.signup_view, name='register'),
    path('auth/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('auth/resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('auth/forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('auth/me/', views.current_user_view, name='current_user'),
    path('user/me/', views.current_user_view, name='user_me'),

    # Profile & Welfare Twin
    path('profile/', views.profile_detail_view, name='profile_detail'),
    path('profile/avatar/', views.profile_avatar_view, name='profile_avatar'),
    path('profile/save-wizard/', views.save_wizard_view, name='save_wizard'),
    path('matching/', views.eligibility_matching_view, name='eligibility_matching'),

    # Document Repository
    path('documents/', views.document_list_create_view, name='documents_list_create'),
    path('documents/upload/', views.document_list_create_view, name='documents_upload'),
    path('documents/save-repository/', views.save_repository_view, name='save_repository'),
    path('documents/<str:doc_id_or_key>/delete/', views.document_delete_view, name='document_delete'),
    path('documents/<str:doc_id_or_key>/', views.document_delete_view, name='document_delete_alt'),

    # Schemes
    path('schemes/', views.scheme_list_view, name='scheme_list'),
    path('schemes/bulk-ingest/', views.bulk_ingest_schemes_view, name='bulk_ingest_schemes'),
    path('schemes/upload-csv/', views.bulk_ingest_schemes_view, name='upload_schemes_csv'),
    path('schemes/<int:scheme_id>/bookmark/', views.scheme_bookmark_view, name='scheme_bookmark'),
    path('schemes/<int:scheme_id>/feedback/', views.scheme_feedback_view, name='scheme_feedback'),
    path('schemes/<int:scheme_id>/report/', views.scheme_report_view, name='scheme_report'),
    path('schemes/<str:scheme_id_or_slug>/', views.scheme_detail_view, name='scheme_detail'),
    path('bookmarks/', views.bookmarks_list_view, name='bookmarks_list'),
    path('chat/', views.chat_assistant_view, name='chat_assistant'),

    # Applications
    path('applications/', views.application_list_create_view, name='application_list_create'),
    path('applications/<str:app_id>/', views.application_detail_view, name='application_detail'),

    # Contact
    path('contact/', views.contact_submit_view, name='contact_submit'),

    # Admin Operations
    path('admin/stats/', views.admin_stats_view, name='admin_stats'),
    path('admin/schemes/', views.admin_schemes_crud_view, name='admin_schemes'),
    path('admin/schemes/<int:scheme_id>/', views.admin_schemes_crud_view, name='admin_schemes_detail'),
    path('admin/verifications/', views.admin_verification_list_view, name='admin_verifications'),
    path('admin/verifications/<str:user_id>/<str:doc_key>/verdict/', views.admin_verification_verdict_view, name='admin_verification_verdict'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/updates/', views.admin_updates_view, name='admin_updates'),
    path('admin/updates/<int:update_id>/<str:action>/', views.admin_updates_view, name='admin_updates_action'),

    # Public Telemetry
    path('public/stats/', views.public_stats_view, name='public_stats'),
]
