import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chord_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory
from api import views
import json

rf = RequestFactory()

print("--- Testing Auth APIs ---")
# Test Login
req = rf.post('/api/auth/login/', json.dumps({'loginId': 'chetan.rawat@example.com', 'loginPass': 'password123', 'role': 'citizen'}), content_type='application/json')
res = views.login_view(req)
assert res.status_code == 200, f"Login failed: {res.content}"
print("✓ Login response:", json.loads(res.content.decode('utf-8'))['message'])

# Test Verify OTP
req = rf.post('/api/auth/verify-otp/', json.dumps({'email_or_phone': 'chetan.rawat@example.com', 'otp': '123456', 'role': 'citizen'}), content_type='application/json')
res = views.verify_otp_view(req)
assert res.status_code == 200, f"OTP verification failed: {res.content}"
token = json.loads(res.content.decode('utf-8'))['token']
print("✓ Verify OTP token generated:", token[:12] + '...')

print("\n--- Testing Profile APIs ---")
# Test Profile Get
req = rf.get('/api/profile/', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.profile_detail_view(req)
assert res.status_code == 200, f"Profile get failed: {res.content}"
profile_data = json.loads(res.content.decode('utf-8'))
print(f"✓ Profile loaded: {profile_data['fullName']}, completeness: {profile_data['completeness']}%")

# Test Profile Update
req = rf.put('/api/profile/', json.dumps({'fullName': 'Chetan Rawat', 'occupation': 'Farmer', 'income': 300000}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.profile_detail_view(req)
assert res.status_code == 200, f"Profile update failed: {res.content}"
print("✓ Profile update success:", json.loads(res.content.decode('utf-8'))['message'])

print("\n--- Testing Schemes APIs ---")
# Test Schemes List
req = rf.get('/api/schemes/?category=Agriculture')
res = views.scheme_list_view(req)
assert res.status_code == 200
schemes = json.loads(res.content.decode('utf-8'))
print(f"✓ Schemes retrieved: {len(schemes)} schemes found")

# Test Scheme Detail
req = rf.get('/api/schemes/1/')
res = views.scheme_detail_view(req, 1)
assert res.status_code == 200
scheme_detail = json.loads(res.content.decode('utf-8'))
print(f"✓ Scheme Detail retrieved: {scheme_detail['name']}")

# Test Feedback
req = rf.post('/api/schemes/1/feedback/', json.dumps({'rating': 5, 'feedbackText': 'Extremely helpful benefit!'}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.scheme_feedback_view(req, 1)
assert res.status_code == 200
print("✓ Feedback recorded:", json.loads(res.content.decode('utf-8'))['message'])

print("\n--- Testing Documents & Applications ---")
# Test Documents List
req = rf.get('/api/documents/', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.document_list_create_view(req)
assert res.status_code == 200
docs = json.loads(res.content.decode('utf-8'))
print(f"✓ Documents retrieved: {len(docs)} documents stored")

# Test Applications List
req = rf.get('/api/applications/', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.application_list_create_view(req)
assert res.status_code == 200
apps_data = json.loads(res.content.decode('utf-8'))
print(f"✓ Applications retrieved: {len(apps_data['applications'])} applications tracked")

# Test Application Create
req = rf.post('/api/applications/', json.dumps({'schemeId': 4, 'schemeName': 'Ayushman Bharat — PM-JAY'}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
res = views.application_list_create_view(req)
assert res.status_code == 201
new_app = json.loads(res.content.decode('utf-8'))
print(f"✓ Application submitted: ID {new_app['applicationId']}")

print("\n--- Testing Contact & Admin APIs ---")
# Test Contact
req = rf.post('/api/contact/', json.dumps({'name': 'Test Citizen', 'email': 'test@example.com', 'subject': 'Feedback', 'message': 'Great platform!'}), content_type='application/json')
res = views.contact_submit_view(req)
assert res.status_code == 200
print("✓ Contact form submitted:", json.loads(res.content.decode('utf-8'))['message'])

# Test Admin Stats
req = rf.get('/api/admin/stats/')
res = views.admin_stats_view(req)
assert res.status_code == 200
stats = json.loads(res.content.decode('utf-8'))
print(f"✓ Admin Stats: {stats['totalSchemes']} schemes, {stats['totalApplications']} applications")

print("\n>>> ALL API TESTS PASSED SUCCESSFULLY! <<<")
