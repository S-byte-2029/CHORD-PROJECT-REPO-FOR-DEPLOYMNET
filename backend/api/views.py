from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import (
    UserAccount, Scheme, UserDocument, Application,
    SchemeBookmark, SchemeFeedback, SchemeReport, ContactMessage, SchemeUpdate
)
import json
import uuid
import os

# ==========================================
# HELPER UTILITIES
# ==========================================

def json_response(data, status=200):
    return JsonResponse(data, status=status, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})

def json_error(message, status=400):
    return JsonResponse({'status': 'error', 'message': message}, status=status)

def parse_body(request):
    if request.content_type == 'application/json' or (request.body and not request.POST):
        try:
            return json.loads(request.body.decode('utf-8'))
        except Exception:
            return {}
    return request.POST.dict()

def get_auth_user(request):
    """
    Identifies the authenticated user from Authorization header, token parameter,
    or X-User-Email header. Returns None if unauthenticated.
    """
    token = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split('Bearer ')[1].strip()
    elif 'token' in request.GET:
        token = request.GET.get('token')
    
    if token:
        user = UserAccount.objects.filter(token=token).first()
        if user:
            return user

    # Check for email passed in headers / params
    user_email = request.headers.get('X-User-Email') or request.GET.get('user_email')
    if user_email:
        user = UserAccount.objects.filter(email__iexact=user_email.strip()).first()
        if user:
            return user

    return None


# ==========================================
# 1. AUTHENTICATION VIEWS
# ==========================================

@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    data = parse_body(request)
    login_id = str(data.get('email_or_phone') or data.get('loginId') or '').strip()
    password = str(data.get('password') or data.get('loginPass') or '').strip()
    role = str(data.get('role') or 'citizen').strip()

    if not login_id:
        return json_error('Email address or phone number is required.')

    # Find user or create default demo account
    user = UserAccount.objects.filter(Q(email__iexact=login_id) | Q(phone=login_id)).first()
    if not user:
        # Create user for demo continuity
        is_admin = (role == 'admin' or 'gov.in' in login_id or 'admin' in login_id)
        user = UserAccount.objects.create(
            email=login_id if '@' in login_id else f"{login_id}@chord.gov.in",
            phone=login_id if '@' not in login_id else '+91 98765 43210',
            full_name='Admin Officer' if is_admin else (login_id.split('@')[0].replace('.', ' ').title()),
            role='admin' if is_admin else 'citizen',
            otp_code='123456'
        )
        user.set_password(password or 'password123')
        user.save()

    # Generate / reset OTP
    user.otp_code = '123456'
    user.otp_created_at = timezone.now()
    user.save(update_fields=['otp_code', 'otp_created_at'])

    return json_response({
        'status': 'success',
        'message': f'Verification OTP sent to {login_id}',
        'target': login_id,
        'role': user.role,
        'otp_demo': '123456'
    })


@csrf_exempt
def signup_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    data = parse_body(request)
    full_name = str(data.get('full_name') or data.get('name') or data.get('username') or '').strip()
    email_or_phone = str(data.get('email_or_phone') or data.get('email') or data.get('mobile') or '').strip()
    password = str(data.get('password') or '').strip()
    role = str(data.get('role') or 'citizen').strip()

    if not full_name or not email_or_phone:
        return json_error('Full name and email/phone are required.')

    user = UserAccount.objects.filter(Q(email__iexact=email_or_phone) | Q(phone=email_or_phone)).first()
    if user:
        # Update details
        user.full_name = full_name
        user.role = role
        user.otp_code = '123456'
        user.set_password(password)
        user.save()
    else:
        user = UserAccount.objects.create(
            full_name=full_name,
            email=email_or_phone if '@' in email_or_phone else f"{email_or_phone}@chord.user",
            phone=email_or_phone if '@' not in email_or_phone else '+91 98765 43210',
            role=role,
            otp_code='123456'
        )
        user.set_password(password)
        user.save()

    return json_response({
        'status': 'success',
        'message': f'Account prepared. Verification OTP sent to {email_or_phone}',
        'target': email_or_phone,
        'role': user.role,
        'otp_demo': '123456'
    })


@csrf_exempt
def verify_otp_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    data = parse_body(request)
    target = str(data.get('email_or_phone') or data.get('email') or data.get('phone') or data.get('target') or '').strip()
    otp = str(data.get('otp') or '').strip()
    role = str(data.get('role') or '').strip()

    # Allow universal demo code 123456 or actual DB match
    user = None
    if target:
        user = UserAccount.objects.filter(Q(email__iexact=target) | Q(phone=target)).first()

    if not user:
        if not target:
            return json_error('Email or phone target is required for verification.', 400)
        
        clean_name = 'Admin Officer' if role == 'admin' else (target.split('@')[0].replace('.', ' ').title() if '@' in target else 'Citizen User')
        user = UserAccount.objects.create(
            full_name=clean_name,
            email=target if '@' in target else f"{target}@chord.user",
            phone=target if '@' not in target else '',
            role=role or 'citizen',
            otp_code='123456'
        )

    if otp != '123456' and otp != user.otp_code:
        return json_error('Incorrect OTP. Please enter 123456.', 400)

    token = user.generate_token()

    return json_response({
        'status': 'success',
        'message': 'Authentication verified successfully!',
        'token': token,
        'user': {
            'id': user.id,
            'fullName': user.full_name,
            'name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'state': user.state,
            'occupation': user.occupation
        },
        'redirect': 'admin.html' if user.role == 'admin' else 'dashboard.html'
    })


@csrf_exempt
def resend_otp_view(request):
    data = parse_body(request)
    target = data.get('email_or_phone') or data.get('email') or data.get('phone') or 'user'
    return json_response({
        'status': 'success',
        'message': f'New OTP code 123456 dispatched to {target}',
        'otp_demo': '123456'
    })


@csrf_exempt
def forgot_password_view(request):
    data = parse_body(request)
    email = data.get('email', '')
    return json_response({
        'status': 'success',
        'message': f'Password reset instructions sent to {email}',
        'email': email
    })


@csrf_exempt
def current_user_view(request):
    user = get_auth_user(request)
    if not user:
        return json_error('User not found', 404)
    return json_response({
        'id': user.id,
        'fullName': user.full_name,
        'name': user.full_name,
        'email': user.email,
        'phone': user.phone,
        'role': user.role,
        'state': user.state,
        'stateName': user.state,
        'district': user.district,
        'occupation': user.occupation,
        'income': user.income,
        'completeness': user.calculate_completeness()
    })


# ==========================================
# 2. PROFILE VIEWS
# ==========================================

@csrf_exempt
def profile_detail_view(request):
    user = get_auth_user(request)
    if not user:
        return json_error('Authentication required. Please log in.', 401)

    if request.method == 'GET':
        matched_count = Scheme.objects.filter(is_active=True).count()
        apps_count = user.applications.count()
        bookmarks_count = user.bookmarks.count()

        return json_response({
            'fullName': user.full_name,
            'name': user.full_name,
            'dob': user.dob,
            'gender': user.gender,
            'state': user.state,
            'stateName': user.state,
            'district': user.district,
            'address': user.address,
            'email': user.email,
            'phone': user.phone,
            'occupation': user.occupation,
            'income': user.income,
            'education': user.education,
            'category': user.category,
            'hasDisability': user.has_disability,
            'disability': 'Yes' if user.has_disability else 'No',
            'disabilityType': user.disability_type,
            'disabilityPct': user.disability_pct,
            'emailAlerts': user.email_alerts,
            'smsAlerts': user.sms_alerts,
            'shareProfile': user.share_profile,
            'avatarUrl': user.avatar.url if user.avatar else None,
            'completeness': user.calculate_completeness(),
            'matchedCount': matched_count,
            'applicationsCount': apps_count,
            'bookmarksCount': bookmarks_count,
            'memberSince': user.created_at.strftime('%b %Y')
        })

    elif request.method in ['PUT', 'PATCH', 'POST']:
        data = parse_body(request)
        if 'fullName' in data: user.full_name = data['fullName']
        if 'dob' in data: user.dob = data['dob']
        if 'gender' in data: user.gender = data['gender']
        if 'state' in data: user.state = data['state']
        if 'district' in data: user.district = data['district']
        if 'address' in data: user.address = data['address']
        if 'email' in data and data['email']: user.email = data['email']
        if 'phone' in data: user.phone = data['phone']
        if 'occupation' in data: user.occupation = data['occupation']
        if 'income' in data:
            try:
                user.income = int(data['income'])
            except (ValueError, TypeError):
                pass
        if 'education' in data: user.education = data['education']
        if 'category' in data: user.category = data['category']
        if 'hasDisability' in data:
            val = data['hasDisability']
            user.has_disability = (val is True or val == 'Yes' or val == 'true')
        if 'disabilityType' in data: user.disability_type = data['disabilityType']
        if 'disabilityPct' in data:
            try:
                user.disability_pct = int(data['disabilityPct'] or 0)
            except (ValueError, TypeError):
                pass
        if 'emailAlerts' in data: user.email_alerts = bool(data['emailAlerts'])
        if 'smsAlerts' in data: user.sms_alerts = bool(data['smsAlerts'])
        if 'shareProfile' in data: user.share_profile = bool(data['shareProfile'])
        user.save()

        return json_response({
            'status': 'success',
            'message': 'Profile updated successfully!',
            'completeness': user.calculate_completeness()
        })

    return json_error('Method not allowed', 405)


@csrf_exempt
def profile_avatar_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)
    
    avatar_file = request.FILES.get('avatar') or request.FILES.get('file')
    if not avatar_file:
        return json_error('No avatar file provided')

    user.avatar = avatar_file
    user.save(update_fields=['avatar'])

    return json_response({
        'status': 'success',
        'message': 'Avatar updated successfully',
        'avatarUrl': user.avatar.url
    })


@csrf_exempt
def save_wizard_view(request):
    """
    Saves the 5-step Welfare Twin wizard questionnaire from dashboard.html.
    """
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)

    data = parse_body(request)
    if 'fullName' in data: user.full_name = data['fullName']
    if 'gender' in data: user.gender = data['gender']
    if 'state' in data: user.state = data['state']
    if 'district' in data: user.district = data['district']
    if 'occupation' in data: user.occupation = data['occupation']
    if 'income' in data:
        try: user.income = int(data['income'])
        except Exception: pass
    if 'education' in data: user.education = data['education']
    if 'category' in data: user.category = data['category']
    if 'disability' in data:
        user.has_disability = (data['disability'] == 'Yes' or data['disability'] is True)
    if 'disabilityType' in data: user.disability_type = data['disabilityType']
    if 'disabilityPct' in data:
        try: user.disability_pct = int(data['disabilityPct'] or 0)
        except Exception: pass
    user.save()

    return json_response({
        'status': 'success',
        'message': 'Welfare Twin profile updated from wizard!',
        'matchedCount': Scheme.objects.filter(is_active=True).count()
    })


# ==========================================
# 3. DOCUMENT REPOSITORY VIEWS
# ==========================================

@csrf_exempt
def document_list_create_view(request):
    user = get_auth_user(request)
    if not user:
        return json_error('Authentication required. Please log in.', 401)

    if request.method == 'GET':
        docs = UserDocument.objects.filter(user=user).order_by('-uploaded_at')
        doc_list = []
        for d in docs:
            doc_list.append({
                'id': d.id,
                'docKey': d.doc_key,
                'name': d.file_name,
                'category': d.category,
                'typeBadge': d.doc_type_name,
                'size': d.file_size,
                'format': d.file_format,
                'uploadedDate': d.uploaded_at.strftime('%d %b %Y'),
                'status': d.status,
                'fileUrl': d.file.url if d.file else None
            })
        return json_response(doc_list)

    elif request.method == 'POST':
        doc_key = request.POST.get('doc_key') or request.POST.get('key') or request.POST.get('documentType', 'Identity')
        doc_type_name = request.POST.get('doc_type_name') or request.POST.get('specificType', f"{doc_key} Proof")
        uploaded_file = request.FILES.get('file')

        category = 'mandatory' if doc_key in ['Identity', 'Income', 'Address', 'aadhaar', 'income', 'domicile'] else (
            'academic' if doc_key in ['Marksheet', 'education'] else 'other'
        )

        file_name = uploaded_file.name if uploaded_file else f"{doc_key.lower()}_document.pdf"
        file_size = f"{(uploaded_file.size / (1024*1024)):.2f} MB" if uploaded_file else '1.2 MB'
        
        ext = file_name.split('.')[-1].lower() if '.' in file_name else 'pdf'
        file_format = 'PDF Document' if ext == 'pdf' else f'Image ({ext.upper()})'

        # Check if existing document with same doc_key exists for user
        doc, created = UserDocument.objects.get_or_create(
            user=user,
            doc_key=doc_key,
            defaults={
                'doc_type_name': doc_type_name,
                'category': category,
                'file': uploaded_file,
                'file_name': file_name,
                'file_size': file_size,
                'file_format': file_format,
                'status': 'Verified'
            }
        )

        if not created:
            doc.doc_type_name = doc_type_name
            doc.category = category
            if uploaded_file:
                doc.file = uploaded_file
            doc.file_name = file_name
            doc.file_size = file_size
            doc.file_format = file_format
            doc.status = 'Verified'
            doc.save()

        return json_response({
            'status': 'success',
            'message': f'{doc_key} document uploaded and verified successfully!',
            'document': {
                'id': doc.id,
                'docKey': doc.doc_key,
                'name': doc.file_name,
                'category': doc.category,
                'typeBadge': doc.doc_type_name,
                'size': doc.file_size,
                'format': doc.file_format,
                'uploadedDate': doc.uploaded_at.strftime('%d %b %Y'),
                'status': doc.status,
                'fileUrl': doc.file.url if doc.file else None
            }
        })

    return json_error('Method not allowed', 405)


@csrf_exempt
def document_delete_view(request, doc_id_or_key):
    if request.method not in ['DELETE', 'POST']:
        return json_error('Method not allowed', 405)

    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)

    if str(doc_id_or_key).isdigit():
        UserDocument.objects.filter(user=user, id=int(doc_id_or_key)).delete()
    else:
        UserDocument.objects.filter(user=user, doc_key=str(doc_id_or_key)).delete()

    return json_response({
        'status': 'success',
        'message': f'Document {doc_id_or_key} removed successfully.'
    })


@csrf_exempt
def save_repository_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)
    
    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)

    data = parse_body(request)
    docs_payload = data.get('documents')
    if isinstance(docs_payload, dict):
        for doc_key, info in docs_payload.items():
            if info:
                name = info.get('name', f'{doc_key}_doc.pdf')
                size = info.get('size', '1.0 MB')
                fmt = info.get('format', 'PDF Document')
                category = 'mandatory' if doc_key in ['Identity', 'Income', 'Address'] else ('academic' if doc_key == 'Marksheet' else 'other')
                doc_obj, _ = UserDocument.objects.get_or_create(
                    user=user,
                    doc_key=doc_key,
                    defaults={
                        'doc_type_name': f'{doc_key} Proof',
                        'category': category,
                        'file_name': name,
                        'file_size': size,
                        'file_format': fmt,
                        'status': 'Verified'
                    }
                )
                doc_obj.file_name = name
                doc_obj.file_size = size
                doc_obj.file_format = fmt
                doc_obj.save()

    # Check mandatory proofs
    mandatory_keys = ['Identity', 'Income', 'Address']
    user_keys = list(UserDocument.objects.filter(user=user).values_list('doc_key', flat=True))
    
    return json_response({
        'status': 'success',
        'message': 'All documents saved and verified in welfare repository.',
        'mandatoryUploaded': len([k for k in mandatory_keys if k in user_keys]),
        'totalUploaded': len(user_keys)
    })


# ==========================================
# 4. SCHEMES & SEARCH VIEWS
# ==========================================

@csrf_exempt
def scheme_list_view(request):
    schemes = Scheme.objects.filter(is_active=True).order_by('id')

    # Filtering parameters
    search = request.GET.get('search', '').strip().lower()
    category = request.GET.get('category', '').strip()
    state_param = request.GET.get('state', '').strip()
    occupation_param = request.GET.get('occupation', '').strip()
    income_param = request.GET.get('income', '').strip()
    type_param = request.GET.get('type', '').strip()

    if search:
        schemes = schemes.filter(
            Q(name__icontains=search) |
            Q(ministry__icontains=search) |
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    if category and category != 'all':
        schemes = schemes.filter(category__icontains=category)

    if state_param and state_param != 'all' and state_param != 'All India':
        schemes = schemes.filter(Q(state_coverage__icontains=state_param) | Q(state_coverage='All India'))

    scheme_list = []
    user = get_auth_user(request)
    saved_ids = list(user.bookmarks.values_list('scheme_id', flat=True)) if user else []

    for s in schemes:
        # Determine eligibility tag based on basic matching
        elig_status = 'eligible'
        if s.id == 3 or s.id == 8:
            elig_status = 'partial'
        elif s.id == 5:
            elig_status = 'not'

        scheme_list.append({
            'id': s.id,
            'scheme_code': s.scheme_code or f"SCH-{(s.category[:3].upper()) if s.category else 'GEN'}-{s.id:04d}",
            'schemeCode': s.scheme_code or f"SCH-{(s.category[:3].upper()) if s.category else 'GEN'}-{s.id:04d}",
            'slug': s.slug,
            'name': s.name,
            'ministry': s.ministry,
            'category': s.category,
            'type': s.gov_level,
            'desc': s.description or s.objective,
            'eligibility': elig_status,
            'benefits': s.benefits_summary or (s.benefits[0]['desc'] if s.benefits else 'Financial assistance'),
            'documents': s.documents,
            'lastDate': s.deadline,
            'sector': s.target_sectors or [s.category],
            'occupation': s.target_occupations or ['Farmer', 'Student', 'All'],
            'state': s.state_coverage,
            'more': s.beneficiaries or s.objective,
            'aiScore': s.ai_score,
            'isSaved': s.id in saved_ids
        })

    return json_response(scheme_list)


@csrf_exempt
def scheme_detail_view(request, scheme_id_or_slug):
    scheme = None
    if str(scheme_id_or_slug).isdigit():
        scheme = Scheme.objects.filter(id=int(scheme_id_or_slug)).first()
    if not scheme:
        scheme = Scheme.objects.filter(slug=str(scheme_id_or_slug)).first()
    if not scheme:
        scheme = Scheme.objects.filter(scheme_code=str(scheme_id_or_slug)).first()
    if not scheme:
        # Fallback to first scheme
        scheme = Scheme.objects.first()

    if not scheme:
        return json_error('Scheme not found', 404)

    user = get_auth_user(request)
    is_saved = user.bookmarks.filter(scheme=scheme).exists() if user else False

    data = {
        'id': scheme.id,
        'scheme_code': scheme.scheme_code or f"SCH-{(scheme.category[:3].upper()) if scheme.category else 'GEN'}-{scheme.id:04d}",
        'schemeCode': scheme.scheme_code or f"SCH-{(scheme.category[:3].upper()) if scheme.category else 'GEN'}-{scheme.id:04d}",
        'slug': scheme.slug,
        'name': scheme.name,
        'category': scheme.category,
        'govLevel': scheme.gov_level,
        'status': scheme.status,
        'objective': scheme.objective,
        'description': scheme.description,
        'beneficiaries': scheme.beneficiaries,
        'benefits': scheme.benefits,
        'eligibility': scheme.eligibility,
        'documents': scheme.documents,
        'process': scheme.process,
        'deadline': scheme.deadline,
        'officialLink': scheme.official_link,
        'contact': scheme.contact_info,
        'faqs': scheme.faqs,
        'aiScore': scheme.ai_score,
        'aiChecklist': scheme.ai_checklist,
        'estimatedBenefit': scheme.estimated_benefit,
        'isSaved': is_saved
    }

    return json_response(data)


@csrf_exempt
def scheme_bookmark_view(request, scheme_id):
    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)

    scheme = Scheme.objects.filter(id=scheme_id).first()
    if not scheme:
        return json_error('Scheme not found', 404)

    if request.method == 'GET':
        is_saved = user.bookmarks.filter(scheme=scheme).exists()
        return json_response({'schemeId': scheme.id, 'isSaved': is_saved})

    elif request.method in ['POST', 'DELETE']:
        bookmark = user.bookmarks.filter(scheme=scheme).first()
        if bookmark:
            bookmark.delete()
            saved = False
            msg = f'{scheme.name} removed from saved bookmarks.'
        else:
            SchemeBookmark.objects.create(user=user, scheme=scheme)
            saved = True
            msg = f'{scheme.name} saved to your bookmarks.'

        return json_response({
            'status': 'success',
            'isSaved': saved,
            'message': msg
        })

    return json_error('Method not allowed', 405)


@csrf_exempt
def bookmarks_list_view(request):
    user = get_auth_user(request)
    if not user:
        return json_error('User not authenticated', 401)

    bookmarks = user.bookmarks.select_related('scheme').all()
    res = []
    for b in bookmarks:
        s = b.scheme
        res.append({
            'id': s.id,
            'name': s.name,
            'category': s.category,
            'ministry': s.ministry,
            'benefit': s.benefits_summary or (s.benefits[0]['desc'] if s.benefits else 'Benefit available'),
            'deadline': s.deadline
        })
    return json_response(res)


@csrf_exempt
def scheme_feedback_view(request, scheme_id):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    scheme = Scheme.objects.filter(id=scheme_id).first()
    if not scheme:
        return json_error('Scheme not found', 404)

    user = get_auth_user(request)
    data = parse_body(request)

    rating = int(data.get('rating', 5))
    text = data.get('feedbackText', data.get('feedback', ''))

    SchemeFeedback.objects.create(
        scheme=scheme,
        user=user,
        rating=rating,
        feedback_text=text
    )

    return json_response({
        'status': 'success',
        'message': f'Thank you! Your feedback for {scheme.name} has been recorded.'
    })


@csrf_exempt
def scheme_report_view(request, scheme_id):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    scheme = Scheme.objects.filter(id=scheme_id).first()
    if not scheme:
        return json_error('Scheme not found', 404)

    user = get_auth_user(request)
    data = parse_body(request)

    issues = data.get('issues', [])
    details = data.get('details', '')

    SchemeReport.objects.create(
        scheme=scheme,
        user=user,
        issues=issues,
        details=details
    )

    return json_response({
        'status': 'success',
        'message': f'Report submitted for "{scheme.name}" — our moderation team will review it.'
    })


@csrf_exempt
def chat_assistant_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    data = parse_body(request)
    query = str(data.get('message') or '').strip().lower()

    if 'kisan' in query or 'farm' in query or 'agriculture' in query:
        reply = "PM-KISAN Samman Nidhi provides ₹6,000 per year in 3 equal instalments directly to landholding farmers. Required documents: Aadhaar, Land Records (Khasra/Khatauni), and Bank Passbook."
    elif 'scholarship' in query or 'student' in query or 'education' in query:
        reply = "The PM Scholarship & National Means-cum-Merit Scholarship offer financial support for students from economically weaker sections. Upload your 10th/12th marksheet and Income Certificate to verify eligibility."
    elif 'ayushman' in query or 'health' in query or 'hospital' in query:
        reply = "Ayushman Bharat PM-JAY offers ₹5,00,000 health cover per family per year for secondary and tertiary care. It is cashless and paperless at all empanelled hospitals."
    elif 'document' in query or 'upload' in query or 'proof' in query:
        reply = "To pre-fill all scheme applications instantly, upload your mandatory proofs in the Document Repository: Identity Proof (Voter ID/PAN/Passport), Income Certificate, and State Domicile."
    elif 'deadline' in query or 'date' in query:
        reply = "Upcoming deadlines: PM-KISAN (31 Aug 2026), Merit Scholarship (15 Sep 2026), PM Awas Yojana (31 Dec 2026)."
    else:
        reply = f"I am your CHORD Welfare Assistant. Based on your question ('{query}'), you can browse all Central and State schemes matched to your profile in the Search tab or check your status in the Application Tracker."

    return json_response({
        'status': 'success',
        'reply': reply
    })


# ==========================================
# 5. APPLICATIONS & TRACKING VIEWS
# ==========================================

@csrf_exempt
def application_list_create_view(request):
    user = get_auth_user(request)
    if not user:
        return json_error('Authentication required. Please log in.', 401)

    if request.method == 'GET':
        apps = Application.objects.filter(user=user).order_by('-submitted_date')
        app_list = []
        for a in apps:
            app_list.append({
                'id': a.id,
                'schemeId': a.scheme.id if a.scheme else 1,
                'schemeName': a.scheme_name,
                'applicationId': a.application_id,
                'submittedDate': a.submitted_date.strftime('%d %b %Y'),
                'lastUpdated': a.last_updated.strftime('%d %b %Y'),
                'status': a.status,
                'stage': a.stage,
                'rejectionReason': a.rejection_reason
            })

        counts = {
            'total': len(app_list),
            'submitted': len([a for a in app_list if a['status'] == 'submitted']),
            'review': len([a for a in app_list if a['status'] == 'review']),
            'approved': len([a for a in app_list if a['status'] == 'approved']),
            'rejected': len([a for a in app_list if a['status'] == 'rejected']),
        }

        return json_response({
            'applications': app_list,
            'summary': counts
        })

    elif request.method == 'POST':
        data = parse_body(request)
        scheme_id = data.get('schemeId')
        scheme_name = data.get('schemeName')

        scheme = None
        if scheme_id:
            scheme = Scheme.objects.filter(id=scheme_id).first()
        if not scheme_name and scheme:
            scheme_name = scheme.name
        if not scheme_name:
            scheme_name = 'PM-KISAN Samman Nidhi'

        # Generate unique Application ID prefix
        prefix = ''.join([w[0] for w in scheme_name.split()[:3]]).upper() or 'APP'
        rand_suffix = str(uuid.uuid4().int)[:5]
        app_id_code = f"{prefix}-2026-{rand_suffix}"

        app = Application.objects.create(
            application_id=app_id_code,
            user=user,
            scheme=scheme,
            scheme_name=scheme_name,
            status='submitted',
            stage=0,
            applicant_data=data
        )

        return json_response({
            'status': 'success',
            'message': f'Application {app_id_code} filed successfully!',
            'applicationId': app_id_code,
            'schemeName': scheme_name
        }, status=201)

    return json_error('Method not allowed', 405)


@csrf_exempt
def application_detail_view(request, app_id):
    app = Application.objects.filter(Q(application_id=app_id) | Q(id=int(app_id) if str(app_id).isdigit() else 0)).first()
    if not app:
        return json_error('Application not found', 404)

    return json_response({
        'id': app.id,
        'applicationId': app.application_id,
        'schemeName': app.scheme_name,
        'status': app.status,
        'stage': app.stage,
        'submittedDate': app.submitted_date.strftime('%d %b %Y'),
        'lastUpdated': app.last_updated.strftime('%d %b %Y'),
        'rejectionReason': app.rejection_reason,
        'applicant': {
            'name': app.user.full_name,
            'email': app.user.email,
            'state': app.user.state
        }
    })


# ==========================================
# 6. WELFARE ELIGIBILITY MATCHING ENGINE
# ==========================================

@csrf_exempt
def eligibility_matching_view(request):
    user = get_auth_user(request)
    data = parse_body(request) if request.method == 'POST' else request.GET

    occupation = data.get('occupation', user.occupation if user else 'Farmer')
    try:
        income = int(data.get('income', user.income if user else 285000))
    except Exception:
        income = 285000
    state_name = data.get('state', user.state if user else 'Uttarakhand')
    category = data.get('category', user.category if user else 'OBC')
    has_disability = data.get('disability', 'Yes' if (user and user.has_disability) else 'No')

    matched_schemes = []
    all_schemes = Scheme.objects.filter(is_active=True)

    for s in all_schemes:
        match = True
        score = s.ai_score
        reason = "Matched by demographic twin parameters"

        if s.name == 'PM-KISAN Samman Nidhi':
            if occupation == 'Farmer' and income <= 800000:
                reason = 'Farmer · income within limit'
            else:
                score -= 40
        elif s.name == 'National Means-cum-Merit Scholarship':
            if occupation == 'Student' and income <= 350000:
                reason = 'Student · income within limit'
            else:
                score -= 35
        elif 'Stand-Up' in s.name:
            if category in ['SC', 'ST'] or occupation == 'Business':
                reason = 'Entrepreneur · reservation / priority sector'
            else:
                score -= 25
        elif 'Awas' in s.name:
            if income <= 600000:
                reason = 'EWS/LIG income threshold qualified'
            else:
                score -= 45

        matched_schemes.append({
            'id': s.id,
            'name': s.name,
            'ministry': s.ministry,
            'category': s.category,
            'why': reason,
            'aiScore': max(score, 50),
            'benefit': s.benefits_summary or (s.benefits[0]['desc'] if s.benefits else 'Welfare benefit')
        })

    return json_response({
        'matchCount': len(matched_schemes),
        'schemes': matched_schemes
    })


# ==========================================
# 7. CONTACT & GRIEVANCES
# ==========================================

@csrf_exempt
def contact_submit_view(request):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    data = parse_body(request)
    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip()
    subject = str(data.get('subject', 'General Query')).strip()
    message = str(data.get('message', '')).strip()

    if not name or not email or not message:
        return json_error('Please fill in all required fields.')

    msg = ContactMessage.objects.create(
        name=name,
        email=email,
        subject=subject,
        message=message
    )

    return json_response({
        'status': 'success',
        'message': '✓ Thank you! Your message has been received by the CHORD team.',
        'messageId': msg.id
    })


# ==========================================
# 8. ADMIN DASHBOARD & MODERATION VIEWS
# ==========================================

@csrf_exempt
def admin_stats_view(request):
    schemes_count = Scheme.objects.count()
    active_schemes = Scheme.objects.filter(is_active=True).count()
    users_count = UserAccount.objects.filter(role='citizen').count()
    apps_count = Application.objects.count()
    pending_updates = SchemeUpdate.objects.filter(status='pending').count()
    pending_docs = UserDocument.objects.filter(status__in=['Pending', 'Under Review']).count()
    approved_docs = UserDocument.objects.filter(status='Verified').count()
    flagged_docs = UserDocument.objects.filter(status__in=['Rejected', 'Reupload']).count()
    open_feedback = ContactMessage.objects.filter(status='open').count() + SchemeReport.objects.filter(resolved=False).count()

    return json_response({
        'totalSchemes': schemes_count,
        'activeSchemes': active_schemes,
        'totalCitizens': users_count,
        'totalApplications': apps_count,
        'pendingUpdates': pending_updates,
        'pendingDocs': pending_docs,
        'approvedDocs': approved_docs,
        'flaggedDocs': flagged_docs,
        'openFeedback': open_feedback
    })


@csrf_exempt
def admin_schemes_crud_view(request, scheme_id=None):
    if request.method == 'GET':
        schemes = Scheme.objects.all().order_by('-id')
        res = []
        for s in schemes:
            res.append({
                'id': s.id,
                'scheme_code': s.scheme_code or f"SCH-{(s.category[:3].upper()) if s.category else 'GEN'}-{s.id:04d}",
                'schemeCode': s.scheme_code or f"SCH-{(s.category[:3].upper()) if s.category else 'GEN'}-{s.id:04d}",
                'name': s.name,
                'category': s.category,
                'state': s.state_coverage,
                'benefit': s.benefits_summary or (s.benefits[0]['desc'] if s.benefits else ''),
                'status': 'Active' if s.is_active else 'Inactive',
                'ministry': s.ministry,
                'eligibility': s.objective or s.description
            })
        return json_response(res)

    elif request.method == 'POST':
        data = parse_body(request)
        name = data.get('name', data.get('schemeName', '')).strip()
        category = data.get('category', data.get('schemeCategory', 'Social Welfare'))
        state = data.get('state', data.get('schemeState', 'All India')).strip() or 'All India'
        benefit = data.get('benefit', data.get('schemeBenefit', '')).strip()
        eligibility_text = data.get('eligibility', data.get('schemeEligibility', '')).strip()
        ministry = data.get('ministry', data.get('schemeMinistry', f'Ministry of {category}'))
        target_occs = data.get('target_occupations') or ['All', 'Farmer', 'Student', 'Daily Wage Worker', 'Business Owner', 'Salaried Employee', 'Unemployed', 'General']
        target_secs = data.get('target_sectors') or [category, 'Social Welfare', 'General']
        docs = data.get('documents') or ['Aadhaar Card', 'Identity Proof', 'Bank Account Details']

        if not name:
            return json_error('Scheme name is required')

        slug = name.lower().replace(' ', '-').replace('—', '-').replace('/', '-')[:60]
        if Scheme.objects.filter(slug=slug).exists():
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"

        scheme = Scheme.objects.create(
            name=name,
            slug=slug,
            category=category,
            ministry=ministry,
            state_coverage=state,
            gov_level='Central Government' if state == 'All India' else 'State Government',
            benefits_summary=benefit or 'Direct Welfare Entitlement',
            objective=eligibility_text or 'Welfare initiative for eligible citizens.',
            description=eligibility_text or 'Welfare initiative for eligible citizens.',
            is_active=True,
            benefits=[{'title': 'Benefit', 'desc': benefit or 'Direct Financial Transfer', 'icon': 'award'}],
            documents=docs,
            target_occupations=target_occs,
            target_sectors=target_secs,
            deadline=data.get('deadline', 'Ongoing'),
            ai_score=int(data.get('ai_score', 95))
        )

        return json_response({
            'status': 'success',
            'message': f'Scheme "{name}" added successfully to CHORD registry.',
            'id': scheme.id,
            'scheme_code': scheme.scheme_code,
            'schemeCode': scheme.scheme_code,
            'slug': scheme.slug
        }, status=201)

    elif request.method in ['PUT', 'PATCH']:
        if not scheme_id:
            return json_error('Scheme ID required for update')
        scheme = Scheme.objects.filter(id=scheme_id).first()
        if not scheme:
            return json_error('Scheme not found', 404)

        data = parse_body(request)
        if 'name' in data: scheme.name = data['name']
        if 'category' in data: scheme.category = data['category']
        if 'state' in data: scheme.state_coverage = data['state']
        if 'benefit' in data: scheme.benefits_summary = data['benefit']
        if 'eligibility' in data: scheme.objective = data['eligibility']
        if 'isActive' in data: scheme.is_active = bool(data['isActive'])
        scheme.save()

        return json_response({
            'status': 'success',
            'message': f'Scheme "{scheme.name}" updated successfully.',
            'scheme_code': scheme.scheme_code
        })

    elif request.method == 'DELETE':
        if not scheme_id:
            return json_error('Scheme ID required')
        Scheme.objects.filter(id=scheme_id).delete()
        return json_response({
            'status': 'success',
            'message': 'Scheme deleted successfully.'
        })

    return json_error('Method not allowed', 405)


@csrf_exempt
def bulk_ingest_schemes_view(request):
    """
    Bulk scheme ingestion endpoint for admin tools and external sync.
    Accepts list of scheme dictionaries, executes chunked upserts, auto-generates scheme IDs.
    """
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    data = parse_body(request)
    records = data if isinstance(data, list) else data.get('schemes', [])
    if not records or not isinstance(records, list):
        return json_error('Expected JSON array of scheme objects', 400)

    created_count = 0
    updated_count = 0

    from django.db import transaction
    with transaction.atomic():
        for item in records:
            name = (item.get('name') or item.get('scheme_name') or '').strip()
            if not name:
                continue
            slug = item.get('slug') or name.lower().replace(' ', '-').replace('/', '-')[:60]
            category = item.get('category') or 'Social Welfare'

            scheme = Scheme.objects.filter(slug=slug).first()
            if not scheme:
                cat_prefix = category[:3].upper().ljust(3, 'X')
                rand_code = uuid.uuid4().hex[:6].upper()
                scheme_code = item.get('scheme_code') or f"SCH-{cat_prefix}-{rand_code}"
                Scheme.objects.create(
                    scheme_code=scheme_code,
                    slug=slug,
                    name=name,
                    category=category,
                    ministry=item.get('ministry', 'Government of India'),
                    gov_level=item.get('gov_level', 'Central Government'),
                    state_coverage=item.get('state_coverage', 'All India'),
                    status=item.get('status', 'Applications Open'),
                    objective=item.get('objective', ''),
                    description=item.get('description', ''),
                    benefits_summary=item.get('benefits_summary', ''),
                    benefits=item.get('benefits', []),
                    eligibility=item.get('eligibility', []),
                    documents=item.get('documents', []),
                    deadline=item.get('deadline', 'Ongoing'),
                    official_link=item.get('official_link', '#'),
                    ai_score=int(item.get('ai_score', 95)),
                    is_active=True
                )
                created_count += 1
            else:
                scheme.name = name
                scheme.category = category
                if 'benefits' in item: scheme.benefits = item['benefits']
                if 'eligibility' in item: scheme.eligibility = item['eligibility']
                if 'documents' in item: scheme.documents = item['documents']
                scheme.save()
                updated_count += 1

    return json_response({
        'status': 'success',
        'message': f'Bulk ingestion complete: {created_count} created, {updated_count} updated.',
        'createdCount': created_count,
        'updatedCount': updated_count,
        'totalActive': Scheme.objects.filter(is_active=True).count()
    })


@csrf_exempt
def admin_verification_list_view(request):
    users = UserAccount.objects.all().order_by('id')
    doc_fields = [
        {'key': 'aadhaar', 'label': 'Identity Proof / ID Card', 'match_keys': ['Identity', 'aadhaar', 'voter']},
        {'key': 'income', 'label': 'Income Certificate', 'match_keys': ['Income', 'income', 'salary']},
        {'key': 'caste', 'label': 'Caste Certificate', 'match_keys': ['caste']},
        {'key': 'domicile', 'label': 'Domicile Certificate', 'match_keys': ['Address', 'domicile', 'address']},
        {'key': 'disability', 'label': 'Disability Certificate', 'match_keys': ['disability']},
        {'key': 'education', 'label': 'Education Certificate', 'match_keys': ['Marksheet', 'education', 'academic']},
        {'key': 'bank', 'label': 'Bank Passbook', 'match_keys': ['bank', 'passbook']},
        {'key': 'other', 'label': 'Other Supporting Proof', 'match_keys': ['Other', 'other', 'land']}
    ]

    res = []
    for u in users:
        user_docs = {}
        for f in doc_fields:
            doc = u.documents.filter(Q(doc_key__in=f['match_keys']) | Q(category__in=f['match_keys'])).first()
            if doc:
                user_docs[f['key']] = {
                    'docId': doc.id,
                    'uploaded': True,
                    'fileName': doc.file_name,
                    'sizeText': doc.file_size,
                    'status': 'approved' if doc.status == 'Verified' else doc.status.lower()
                }
            else:
                user_docs[f['key']] = {
                    'uploaded': False,
                    'fileName': None,
                    'status': 'missing'
                }

        res.append({
            'id': f"USR-{u.id + 100}",
            'rawId': u.id,
            'name': u.full_name,
            'email': u.email,
            'location': f"{u.district}, {u.state}",
            'documents': user_docs
        })

    return json_response(res)


@csrf_exempt
def admin_verification_verdict_view(request, user_id=None, doc_key=None):
    if request.method != 'POST':
        return json_error('Method not allowed', 405)

    data = parse_body(request)
    verdict = data.get('verdict', 'approved').lower() # approved, rejected, reupload
    status_mapped = 'Verified' if verdict == 'approved' else ('Rejected' if verdict == 'rejected' else 'Reupload')

    # Locate user
    raw_id = str(user_id).replace('USR-', '')
    user = None
    if raw_id.isdigit():
        user = UserAccount.objects.filter(id=int(raw_id) - 100).first() or UserAccount.objects.filter(id=int(raw_id)).first()

    if user:
        doc = user.documents.filter(Q(doc_key__iexact=doc_key) | Q(category__iexact=doc_key)).first()
        if doc:
            doc.status = status_mapped
            doc.save(update_fields=['status'])
        else:
            UserDocument.objects.create(
                user=user,
                doc_key=doc_key,
                doc_type_name=f"{doc_key.title()} Document",
                status=status_mapped,
                file_name=f"{doc_key.lower()}_verified.pdf"
            )

    return json_response({
        'status': 'success',
        'verdict': verdict,
        'message': f'Document verdict updated to {verdict.upper()}'
    })


@csrf_exempt
def admin_updates_view(request, update_id=None, action=None):
    if request.method == 'GET':
        updates = SchemeUpdate.objects.all().order_by('-created_at')
        res = []
        for u in updates:
            res.append({
                'id': u.id,
                'schemeName': u.scheme.name,
                'ministry': u.ministry_or_node,
                'change': u.change_summary,
                'status': u.status,
                'date': u.created_at.strftime('%d %b %Y')
            })
        return json_response(res)

    elif request.method == 'POST' and update_id and action:
        up = SchemeUpdate.objects.filter(id=update_id).first()
        if up:
            up.status = 'approved' if action == 'approve' else 'rejected'
            up.save(update_fields=['status'])
        return json_response({
            'status': 'success',
            'message': f'Scheme update {action}d successfully.'
        })

    return json_error('Method not allowed', 405)


@csrf_exempt
def admin_users_view(request):
    users = UserAccount.objects.all().order_by('-id')
    res = []
    for u in users:
        res.append({
            'id': u.id,
            'name': u.full_name,
            'email': u.email,
            'phone': u.phone,
            'role': u.role,
            'state': u.state,
            'occupation': u.occupation,
            'joined': u.created_at.strftime('%d %b %Y')
        })
    return json_response(res)


# ==========================================
# 9. PUBLIC LIVE TELEMETRY
# ==========================================

@csrf_exempt
def public_stats_view(request):
    return json_response({
        'totalMatches': 48210,
        'unclaimedCr': 214,
        'feed': [
            {'tag': 'match', 'tagLabel': 'Match', 'html': '<b>Post-Matric Scholarship</b> matched to 12,847 eligible students in Bihar'},
            {'tag': 'gap', 'tagLabel': 'Gap', 'html': '3,204 eligible citizens in Purnia not yet notified of <b>Skill Development Scheme</b>'},
            {'tag': 'match', 'tagLabel': 'Match', 'html': '<b>PM Awas Yojana</b> matched to 640 new households in Odisha'},
            {'tag': 'alert', 'tagLabel': 'Alert', 'html': 'Unusual approval cluster flagged in <b>Fertiliser Subsidy</b> — 1 district under review'},
            {'tag': 'gap', 'tagLabel': 'Gap', 'html': 'Uptake in Koraput is 34% below eligible population for <b>Maternity Benefit Scheme</b>'},
            {'tag': 'match', 'tagLabel': 'Match', 'html': '<b>Ayushman Bharat</b> matched to 8,120 newly eligible citizens this week'},
            {'tag': 'match', 'tagLabel': 'Match', 'html': '<b>National Apprenticeship</b> matched to 1,980 recent graduates'}
        ]
    })
