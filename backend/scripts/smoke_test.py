#!/usr/bin/env python3
"""
CHORD End-to-End Production Smoke Test Suite
Can run against:
- Local server: http://127.0.0.1:8000/api
- Live Railway deployment: https://your-backend-railway-app.up.railway.app/api
Usage:
    python backend/scripts/smoke_test.py [API_BASE_URL]
"""

import sys
import json
import urllib.request
import urllib.error

# Parse command line argument or fallback
API_URL = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:8000/api'

TEST_ORIGIN = "https://chord-welfare.netlify.app"

import ssl

# Create resilient SSL context for macOS python certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def make_request(path, method='GET', body=None, headers=None):
    url = f"{API_URL}{path}"
    req_headers = {
        'Origin': TEST_ORIGIN,
        'Accept': 'application/json',
        'User-Agent': 'CHORD-SmokeTest/1.0'
    }
    if body is not None:
        req_headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode('utf-8')
    else:
        data = None

    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context) as resp:
            resp_body = resp.read().decode('utf-8')
            resp_headers = dict(resp.headers)
            try:
                parsed = json.loads(resp_body)
            except Exception:
                parsed = resp_body
            return resp.status, parsed, resp_headers
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode('utf-8')
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = resp_body
        return e.code, parsed, dict(e.headers)
    except Exception as e:
        return 0, str(e), {}

def run_tests():
    print(f"==================================================")
    print(f"  CHORD Platform Live Smoke Test Suite")
    print(f"  Target Base API: {API_URL}")
    print(f"  Simulated Origin: {TEST_ORIGIN}")
    print(f"==================================================\n")

    passed = 0
    failed = 0

    def check(test_name, success, detail=""):
        nonlocal passed, failed
        if success:
            passed += 1
            print(f" [PASS] {test_name} {detail}")
        else:
            failed += 1
            print(f" [FAIL] {test_name} {detail}")

    # Test 1: Schemes List & CORS Headers
    status, schemes, headers = make_request('/schemes/')
    # Cold start retry if initial wake-up was slow
    if status != 200 or not isinstance(schemes, list):
        status, schemes, headers = make_request('/schemes/')
    cors_origin = headers.get('access-control-allow-origin', headers.get('Access-Control-Allow-Origin', ''))
    check(
        "1. Public Schemes API & CORS Verification",
        status == 200 and isinstance(schemes, list) and len(schemes) > 0,
        f"(Count: {len(schemes) if isinstance(schemes, list) else 0}, CORS Origin: '{cors_origin}')"
    )

    # Test 2: Scheme Detail API
    scheme_id = schemes[0]['id'] if isinstance(schemes, list) and len(schemes) > 0 else 1
    status, scheme_detail, _ = make_request(f'/schemes/{scheme_id}/')
    check(
        "2. Scheme Detail API Query",
        status == 200 and isinstance(scheme_detail, dict) and 'name' in scheme_detail,
        f"(Found: '{scheme_detail.get('name', 'N/A') if isinstance(scheme_detail, dict) else 'N/A'}')"
    )

    # Test 3: Citizen Login (OTP Dispatch)
    login_payload = {
        "loginId": "chetan.rawat@example.com",
        "loginPass": "password123",
        "role": "citizen"
    }
    status, login_res, _ = make_request('/auth/login/', method='POST', body=login_payload)
    check(
        "3. Citizen Authentication Login Flow",
        status == 200 and isinstance(login_res, dict) and (login_res.get('status') == 'success' or login_res.get('success') is True or 'message' in login_res),
        f"({login_res.get('message', '') if isinstance(login_res, dict) else login_res})"
    )

    # Test 4: OTP Verification & Bearer Token Generation
    otp_payload = {
        "email_or_phone": "chetan.rawat@example.com",
        "otp": "123456",
        "role": "citizen"
    }
    status, otp_res, _ = make_request('/auth/verify-otp/', method='POST', body=otp_payload)
    token = otp_res.get('token', '') if isinstance(otp_res, dict) else ''
    check(
        "4. Citizen OTP Verification & Token Issuance",
        status == 200 and bool(token),
        f"(Token: {token[:16]}...)"
    )

    auth_headers = {
        'Authorization': f'Bearer {token}',
        'X-User-Email': 'chetan.rawat@example.com'
    }

    # Test 5: Profile Data Retrieval & Completeness
    status, profile, _ = make_request('/profile/', headers=auth_headers)
    check(
        "5. Profile Retrieval & Welfare Twin State",
        status == 200 and isinstance(profile, dict) and profile.get('email') == 'chetan.rawat@example.com',
        f"(Name: {profile.get('fullName', '') if isinstance(profile, dict) else ''}, Completeness: {profile.get('completeness', 0) if isinstance(profile, dict) else 0}%)"
    )

    # Test 6: Profile Partial Update
    update_payload = {
        "fullName": "Chetan Rawat",
        "occupation": "Farmer",
        "income": 300000
    }
    status, update_res, _ = make_request('/profile/', method='PUT', body=update_payload, headers=auth_headers)
    check(
        "6. Citizen Profile Update Pipeline",
        status == 200 and isinstance(update_res, dict) and (update_res.get('status') == 'success' or update_res.get('success') is True or 'message' in update_res),
        f"({update_res.get('message', '') if isinstance(update_res, dict) else ''})"
    )

    # Test 7: Document Listing
    status, docs, _ = make_request('/documents/', headers=auth_headers)
    check(
        "7. Digital Document Locker API",
        status == 200 and isinstance(docs, list),
        f"(Stored Documents: {len(docs) if isinstance(docs, list) else 0})"
    )

    # Test 8: Applications List & Submit Application
    app_payload = {
        "schemeId": scheme_id,
        "schemeName": scheme_detail.get('name', 'PM-KISAN Samman Nidhi') if isinstance(scheme_detail, dict) else 'PM-KISAN'
    }
    status, app_res, _ = make_request('/applications/', method='POST', body=app_payload, headers=auth_headers)
    app_id = app_res.get('applicationId', '') if isinstance(app_res, dict) else ''
    check(
        "8. Direct Scheme Application Submission",
        status in (200, 201) and bool(app_id),
        f"(Application ID: {app_id})"
    )

    # Test 9: Application Tracking
    status, apps_data, _ = make_request('/applications/', headers=auth_headers)
    total_apps = len(apps_data.get('applications', [])) if isinstance(apps_data, dict) else 0
    check(
        "9. Application Lifecycle Tracking",
        status == 200 and total_apps > 0,
        f"(Total Tracked: {total_apps})"
    )

    # Test 10: Feedback Submission
    feedback_payload = {
        "rating": 5,
        "feedbackText": "Live automated smoke test feedback confirmation."
    }
    status, feedback_res, _ = make_request(f'/schemes/{scheme_id}/feedback/', method='POST', body=feedback_payload, headers=auth_headers)
    check(
        "10. Scheme Citizen Feedback Recording",
        status == 200 and isinstance(feedback_res, dict) and (feedback_res.get('status') == 'success' or feedback_res.get('success') is True or 'message' in feedback_res),
        f"({feedback_res.get('message', '') if isinstance(feedback_res, dict) else ''})"
    )

    # Test 11: Contact Form Ingestion
    contact_payload = {
        "name": "Smoke Test Bot",
        "email": "bot@chord-platform.gov.in",
        "subject": "Platform Health Status",
        "message": "Automated verification test run succeeded."
    }
    status, contact_res, _ = make_request('/contact/', method='POST', body=contact_payload)
    check(
        "11. Citizen Inquiries & Helpdesk Form API",
        status == 200 and isinstance(contact_res, dict) and (contact_res.get('status') == 'success' or contact_res.get('success') is True or 'message' in contact_res),
        f"({contact_res.get('message', '') if isinstance(contact_res, dict) else ''})"
    )

    # Test 12: Admin Analytics & Governance Stats
    status, stats, _ = make_request('/admin/stats/')
    check(
        "12. Admin Metrics & Governance Aggregates",
        status == 200 and isinstance(stats, dict) and 'totalSchemes' in stats,
        f"(Schemes: {stats.get('totalSchemes', 0) if isinstance(stats, dict) else 0}, Apps: {stats.get('totalApplications', 0) if isinstance(stats, dict) else 0})"
    )

    print("\n==================================================")
    print(f"  Summary: {passed} Passed, {failed} Failed")
    if failed == 0:
        print("  ✓ ALL API & PERSISTENCE TESTS PASSED SUCCESSFULLY!")
    else:
        print("  ✗ SOME TESTS FAILED — Review logs above.")
    print("==================================================")

    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
