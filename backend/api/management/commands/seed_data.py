import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path when invoked directly or via Render
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chord_backend.settings')

import django
from django.apps import apps
if not apps.ready:
    django.setup()

from django.core.management.base import BaseCommand
from api.models import (
    UserAccount, Scheme, UserDocument, Application,
    SchemeBookmark, SchemeFeedback, SchemeReport, ContactMessage, SchemeUpdate
)
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds initial government schemes, citizen accounts, documents, and applications.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with CHORD data...')

        # 1. Users
        chetan, _ = UserAccount.objects.get_or_create(
            email='chetan.rawat@example.com',
            defaults={
                'full_name': 'Chetan Rawat',
                'phone': '+91 98765 43210',
                'role': 'citizen',
                'dob': '1998-06-14',
                'gender': 'Male',
                'state': 'Uttarakhand',
                'district': 'Dehradun',
                'address': '14, Rajpur Road, Dehradun, Uttarakhand — 248001',
                'occupation': 'Farmer',
                'income': 285000,
                'education': '12th Pass',
                'category': 'OBC',
                'has_disability': False,
                'email_alerts': True,
                'sms_alerts': True,
                'otp_code': '123456'
            }
        )
        chetan.set_password('password123')
        chetan.save()

        admin_user, _ = UserAccount.objects.get_or_create(
            email='admin.officer@gov.in',
            defaults={
                'full_name': 'Admin Officer',
                'phone': '+91 91234 56789',
                'role': 'admin',
                'state': 'Delhi',
                'district': 'New Delhi',
                'occupation': 'Salaried',
                'otp_code': '123456'
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        rahul, _ = UserAccount.objects.get_or_create(
            email='rahul@example.com',
            defaults={
                'full_name': 'Rahul Sharma',
                'phone': '+91 98222 11111',
                'role': 'citizen',
                'state': 'Bihar',
                'district': 'Purnia',
                'occupation': 'Student',
                'income': 180000,
                'category': 'General',
                'otp_code': '123456'
            }
        )

        priya, _ = UserAccount.objects.get_or_create(
            email='priya@example.com',
            defaults={
                'full_name': 'Priya Singh',
                'phone': '+91 98333 22222',
                'role': 'citizen',
                'state': 'Rajasthan',
                'district': 'Jaipur',
                'occupation': 'Business',
                'income': 450000,
                'category': 'SC',
                'otp_code': '123456'
            }
        )

        # 2. Schemes
        schemes_data = [
            {
                'id': 1,
                'slug': 'pm-kisan',
                'name': 'PM-KISAN Samman Nidhi',
                'ministry': 'Ministry of Agriculture',
                'category': 'Agriculture',
                'gov_level': 'Central',
                'state_coverage': 'Bihar',
                'desc': 'Income support of ₹6,000/year to landholding farmer families, paid in three instalments.',
                'benefits_summary': '₹6,000 per year direct transfer',
                'benefits': [
                    {'title': 'Direct Income Support', 'desc': '₹6,000 per year', 'icon': 'coin'},
                    {'title': 'Three Instalments', 'desc': '₹2,000 paid every 4 months', 'icon': 'calendar'},
                    {'title': 'Direct Bank Transfer', 'desc': 'No intermediaries', 'icon': 'bank'}
                ],
                'eligibility': [
                    {'title': 'Indian Citizen', 'desc': 'Must hold valid Indian citizenship', 'icon': 'flag'},
                    {'title': 'Landholding Farmer', 'desc': 'Owns cultivable agricultural land', 'icon': 'leaf'},
                    {'title': 'Valid Land Records', 'desc': 'Land ownership must be documented', 'icon': 'doc'}
                ],
                'documents': ['Aadhaar Card', 'Land Records', 'Bank Passbook'],
                'process': [
                    {'title': 'Register', 'desc': 'Register on the PM-KISAN portal.'},
                    {'title': 'Upload Documents', 'desc': 'Submit Aadhaar and land records.'},
                    {'title': 'Verification', 'desc': 'State authorities verify landholding details.'},
                    {'title': 'Approval', 'desc': 'Application is approved for disbursal.'},
                    {'title': 'Receive Benefits', 'desc': 'Instalments credited directly to your bank account.'}
                ],
                'deadline': '31 Aug 2026',
                'ai_score': 96,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Education Eligible', 'pass': True}
                ],
                'estimated_benefit': '₹6,000/year',
                'target_occupations': ['Farmer'],
                'target_sectors': ['Agriculture']
            },
            {
                'id': 2,
                'slug': 'national-means-cum-merit-scholarship',
                'name': 'National Means-cum-Merit Scholarship',
                'ministry': 'Ministry of Education',
                'category': 'Education',
                'gov_level': 'Central',
                'state_coverage': 'Uttar Pradesh',
                'desc': 'Scholarship for meritorious students from economically weaker sections to reduce dropout at class 9.',
                'benefits_summary': '₹12,000 per year',
                'benefits': [
                    {'title': 'Annual Scholarship', 'desc': '₹12,000 per year (₹1,000/month)', 'icon': 'award'},
                    {'title': 'Direct Bank Disbursal', 'desc': 'Via National Scholarship Portal (NSP)', 'icon': 'bank'},
                    {'title': 'Renewable', 'desc': 'Up to Class 12 based on performance', 'icon': 'receipt'}
                ],
                'eligibility': [
                    {'title': 'Class 8 Student', 'desc': 'Enrolled in a State Govt / Aided School', 'icon': 'book'},
                    {'title': 'Family Income', 'desc': 'Below ₹3.5 lakh per annum', 'icon': 'coin'},
                    {'title': 'Qualifying Exam', 'desc': 'Minimum 55% in Class 7 & qualifying NMMSS exam', 'icon': 'check'}
                ],
                'documents': ['Aadhaar Card', 'Income Certificate', 'Marksheet'],
                'process': [
                    {'title': 'Apply on NSP', 'desc': 'Register at scholarships.gov.in.'},
                    {'title': 'Appear for Exam', 'desc': 'State-level selection test.'},
                    {'title': 'Merit List', 'desc': 'Selected students uploaded to portal.'},
                    {'title': 'Annual Disbursal', 'desc': 'Amount credited every quarter.'}
                ],
                'deadline': '15 Sep 2026',
                'ai_score': 92,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Education Eligible', 'pass': True}
                ],
                'estimated_benefit': '₹12,000/year',
                'target_occupations': ['Student'],
                'target_sectors': ['Education']
            },
            {
                'id': 3,
                'slug': 'stand-up-india',
                'name': 'Stand-Up India Scheme',
                'ministry': 'Ministry of Skill Development',
                'category': 'Employment',
                'gov_level': 'Central',
                'state_coverage': 'Maharashtra',
                'desc': 'Bank loans between ₹10 lakh and ₹1 crore for SC/ST and women entrepreneurs setting up greenfield enterprises.',
                'benefits_summary': 'Loans from ₹10L to ₹1Cr',
                'benefits': [
                    {'title': 'Composite Loan', 'desc': 'Between ₹10 lakh and ₹1 crore', 'icon': 'coin'},
                    {'title': 'Working Capital', 'desc': 'Overdraft facility up to ₹10 lakh', 'icon': 'bank'},
                    {'title': 'Lower Margin Money', 'desc': 'Up to 15% with convergence', 'icon': 'award'}
                ],
                'eligibility': [
                    {'title': 'Category', 'desc': 'SC/ST and/or Woman Entrepreneur', 'icon': 'flag'},
                    {'title': 'Age', 'desc': 'Above 18 years', 'icon': 'check'},
                    {'title': 'Greenfield Project', 'desc': 'First-time venture in manufacturing or services', 'icon': 'doc'}
                ],
                'documents': ['Business Plan', 'Aadhaar Card', 'Caste Certificate (if applicable)'],
                'process': [
                    {'title': 'Submit Proposal', 'desc': 'Apply at standupmitra.in or lead bank.'},
                    {'title': 'Project Appraisal', 'desc': 'Bank evaluates techno-financial viability.'},
                    {'title': 'Sanction & Disbursal', 'desc': 'Composite loan released.'}
                ],
                'deadline': 'Rolling',
                'ai_score': 74,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'Enterprise Category', 'pass': False},
                    {'label': 'Project Plan Submitted', 'pass': False}
                ],
                'estimated_benefit': '₹10L – ₹1Cr',
                'target_occupations': ['Business Owner', 'Salaried'],
                'target_sectors': ['Startup', 'Employment']
            },
            {
                'id': 4,
                'slug': 'ayushman-bharat',
                'name': 'Ayushman Bharat — PM-JAY',
                'ministry': 'Ministry of Health',
                'category': 'Healthcare',
                'gov_level': 'Central',
                'state_coverage': 'Odisha',
                'desc': 'Health cover of ₹5 lakh per family per year for secondary and tertiary care hospitalisation.',
                'benefits_summary': '₹5,00,000 health cover/year',
                'benefits': [
                    {'title': 'Cashless Hospitalisation', 'desc': 'Up to ₹5 lakh per family per year', 'icon': 'award'},
                    {'title': 'Pre & Post Care', 'desc': '3 days pre and 15 days post hospitalization covered', 'icon': 'receipt'},
                    {'title': 'Pan-India Portability', 'desc': 'Treatment at any empanelled hospital nationwide', 'icon': 'flag'}
                ],
                'eligibility': [
                    {'title': 'SECC Beneficiary', 'desc': 'Identified under deprivation criteria SECC 2011', 'icon': 'check'},
                    {'title': 'No Age Limit', 'desc': 'All family members covered', 'icon': 'flag'},
                    {'title': 'No Pre-existing Exclusions', 'desc': 'All pre-existing conditions covered from day 1', 'icon': 'doc'}
                ],
                'documents': ['Aadhaar Card', 'Ration Card', 'Income Certificate'],
                'process': [
                    {'title': 'Check Eligibility', 'desc': 'Search mobile/ration card on pmjay.gov.in.'},
                    {'title': 'Generate Golden Card', 'desc': 'Visit Ayushman Kendra or CSC.'},
                    {'title': 'Avail Treatment', 'desc': 'Cashless admission at empanelled hospital.'}
                ],
                'deadline': 'Ongoing',
                'ai_score': 98,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Identity Proof Verified', 'pass': True}
                ],
                'estimated_benefit': '₹5,00,000/year',
                'target_occupations': ['Farmer', 'Student', 'Business Owner', 'Daily Wage Worker'],
                'target_sectors': ['Health', 'Social Welfare']
            },
            {
                'id': 5,
                'slug': 'pm-awas-yojana',
                'name': 'Pradhan Mantri Awas Yojana',
                'ministry': 'Ministry of Housing & Urban Affairs',
                'category': 'Housing',
                'gov_level': 'Central',
                'state_coverage': 'Rajasthan',
                'desc': 'Interest subsidy on home loans for first-time homebuyers from EWS, LIG, and MIG categories.',
                'benefits_summary': 'Up to ₹2.67 lakh interest subsidy',
                'benefits': [
                    {'title': 'Credit Linked Subsidy', 'desc': 'Up to ₹2.67 lakh upfront on home loan interest', 'icon': 'coin'},
                    {'title': 'Pucca House Assistance', 'desc': '₹1.20L direct assistance in rural areas', 'icon': 'home'}
                ],
                'eligibility': [
                    {'title': 'No Pucca House', 'desc': 'Beneficiary family must not own a pucca house anywhere in India', 'icon': 'home'},
                    {'title': 'Income Limit', 'desc': 'EWS up to ₹3L, LIG up to ₹6L', 'icon': 'coin'}
                ],
                'documents': ['Aadhaar Card', 'Income Certificate', 'Property Documents'],
                'process': [
                    {'title': 'Apply via Bank / CSC', 'desc': 'Submit loan application under CLSS.'},
                    {'title': 'Verification', 'desc': 'Nodal Agency validates eligibility.'},
                    {'title': 'Subsidy Credit', 'desc': 'Directly credited to loan account.'}
                ],
                'deadline': '31 Dec 2026',
                'ai_score': 62,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Housing Status', 'pass': False},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Property Papers', 'pass': False}
                ],
                'estimated_benefit': '₹2.67 Lakh subsidy',
                'target_occupations': ['Salaried', 'Business Owner', 'DailyWage'],
                'target_sectors': ['Housing']
            },
            {
                'id': 6,
                'slug': 'sukanya-samriddhi',
                'name': 'Beti Bachao Beti Padhao — Sukanya Samriddhi',
                'ministry': 'Ministry of Women & Child Development',
                'category': 'Women & Child',
                'gov_level': 'Central',
                'state_coverage': 'Tamil Nadu',
                'desc': 'High-interest savings scheme for the education and marriage expenses of a girl child.',
                'benefits_summary': '7.6% p.a. tax-free interest',
                'benefits': [
                    {'title': 'High Interest Rate', 'desc': 'Attractive government-backed compounding interest', 'icon': 'coin'},
                    {'title': 'Tax Exemption', 'desc': 'Triple tax benefit under Section 80C', 'icon': 'award'}
                ],
                'eligibility': [
                    {'title': 'Girl Child', 'desc': 'Below 10 years of age at time of account opening', 'icon': 'flag'},
                    {'title': 'Legal Guardian', 'desc': 'Opened by parents or natural guardian', 'icon': 'doc'}
                ],
                'documents': ['Birth Certificate', 'Aadhaar Card', 'Guardian ID'],
                'process': [
                    {'title': 'Visit Post Office/Bank', 'desc': 'Submit SSY application form.'},
                    {'title': 'Initial Deposit', 'desc': 'Minimum ₹250 deposit.'},
                    {'title': 'Passbook Issued', 'desc': 'Operated until child turns 18 or 21.'}
                ],
                'deadline': 'Ongoing',
                'ai_score': 90,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Identity Proof', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Child Age Verified', 'pass': True}
                ],
                'estimated_benefit': '7.6% interest',
                'target_occupations': ['Student', 'All'],
                'target_sectors': ['Women', 'Education']
            },
            {
                'id': 7,
                'slug': 'atal-pension-yojana',
                'name': 'Atal Pension Yojana',
                'ministry': 'Ministry of Skill Development',
                'category': 'Social Welfare',
                'gov_level': 'Central',
                'state_coverage': 'West Bengal',
                'desc': 'Guaranteed monthly pension between ₹1,000–₹5,000 for workers in the unorganised sector after age 60.',
                'benefits_summary': '₹1,000–₹5,000 monthly pension',
                'benefits': [
                    {'title': 'Guaranteed Pension', 'desc': 'Fixed monthly pension from age 60', 'icon': 'coin'},
                    {'title': 'Spouse & Nominee Protection', 'desc': 'Pension continues to spouse after subscriber death', 'icon': 'flag'}
                ],
                'eligibility': [
                    {'title': 'Age 18 to 40', 'desc': 'Available for Indian citizens between 18-40 years', 'icon': 'check'},
                    {'title': 'Savings Account', 'desc': 'Requires bank account linked with auto-debit', 'icon': 'bank'}
                ],
                'documents': ['Aadhaar Card', 'Bank Account', 'Mobile Number'],
                'process': [
                    {'title': 'Fill APY Form', 'desc': 'Apply through internet banking or branch.'},
                    {'title': 'Auto Debit Setup', 'desc': 'Monthly contribution auto-deducted.'},
                    {'title': 'PRAN Generated', 'desc': 'Permanent Retirement Account Number issued.'}
                ],
                'deadline': 'Ongoing',
                'ai_score': 94,
                'ai_checklist': [
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'Bank Account Linked', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Identity Proof', 'pass': True}
                ],
                'estimated_benefit': '₹1k–₹5k/month',
                'target_occupations': ['Farmer', 'Daily Wage Worker', 'Salaried'],
                'target_sectors': ['Pension', 'Employment']
            },
            {
                'id': 8,
                'slug': 'national-apprenticeship-promotion-scheme',
                'name': 'National Apprenticeship Promotion Scheme',
                'ministry': 'Ministry of Skill Development',
                'category': 'Employment',
                'gov_level': 'Central',
                'state_coverage': 'Karnataka',
                'desc': 'Financial support to employers for engaging apprentices and building industry-ready skills.',
                'benefits_summary': '25% stipend reimbursement',
                'benefits': [
                    {'title': 'Stipend Support', 'desc': 'Government shares 25% of prescribed stipend up to ₹1,500/month', 'icon': 'coin'},
                    {'title': 'Industry Certification', 'desc': 'National Apprenticeship Certificate upon completion', 'icon': 'award'}
                ],
                'eligibility': [
                    {'title': 'Age 14+', 'desc': 'Minimum 14 years of age (18 for designated trades)', 'icon': 'check'},
                    {'title': 'Educational Qualification', 'desc': 'Passed 5th / 8th / 10th / 12th or ITI / Diploma / Degree', 'icon': 'book'}
                ],
                'documents': ['Aadhaar Card', 'Educational Certificates'],
                'process': [
                    {'title': 'Register on Portal', 'desc': 'Sign up on apprenticeshipindia.gov.in.'},
                    {'title': 'Apply for Contracts', 'desc': 'Search industry apprenticeship vacancies.'},
                    {'title': 'Start Training', 'desc': 'On-the-job training with monthly stipend.'}
                ],
                'deadline': '30 Nov 2026',
                'ai_score': 80,
                'ai_checklist': [
                    {'label': 'Education Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'Enrolled with Establishment', 'pass': False},
                    {'label': 'Identity Verified', 'pass': True}
                ],
                'estimated_benefit': '25% stipend reimbursement',
                'target_occupations': ['Student', 'Unemployed'],
                'target_sectors': ['Employment', 'Education']
            },
            {
                'id': 101,
                'slug': 'pm-scholarship',
                'name': 'PM Scholarship Scheme',
                'ministry': 'Ministry of Education',
                'category': 'Education',
                'gov_level': 'Central Government',
                'state_coverage': 'All India',
                'desc': 'The PM Scholarship Scheme supports students pursuing higher education by covering tuition costs, hostel fees, and other academic expenses.',
                'benefits_summary': '₹75,000 per year',
                'benefits': [
                    {'title': 'Scholarship Amount', 'desc': '₹75,000 per year', 'icon': 'award'},
                    {'title': 'Financial Assistance', 'desc': 'Covers tuition and academic costs', 'icon': 'coin'},
                    {'title': 'Hostel Support', 'desc': 'Partial hostel fee coverage', 'icon': 'home'},
                    {'title': 'Fee Reimbursement', 'desc': 'Reimbursement of eligible fees', 'icon': 'receipt'}
                ],
                'eligibility': [
                    {'title': 'Indian Citizen', 'desc': 'Must hold valid Indian citizenship', 'icon': 'flag'},
                    {'title': 'Income below ₹2.5 lakh', 'desc': 'Annual family income limit', 'icon': 'coin'},
                    {'title': 'Student', 'desc': 'Enrolled in a recognised institution', 'icon': 'book'},
                    {'title': 'Minimum 60%', 'desc': 'In the qualifying examination', 'icon': 'check'}
                ],
                'documents': ['Aadhaar Card', 'Income Certificate', 'Bank Passbook', 'Passport Photo', 'Marksheet'],
                'process': [
                    {'title': 'Register', 'desc': 'Create an account on the scholarship portal.'},
                    {'title': 'Upload Documents', 'desc': 'Submit Aadhaar, income certificate, and marksheets.'},
                    {'title': 'Verification', 'desc': 'Application is verified by the concerned department.'},
                    {'title': 'Approval', 'desc': 'Verified applications are approved for disbursal.'},
                    {'title': 'Receive Benefits', 'desc': 'Scholarship amount is credited directly to your account.'}
                ],
                'deadline': '31 December 2026',
                'ai_score': 95,
                'ai_checklist': [
                    {'label': 'Income Eligible', 'pass': True},
                    {'label': 'Age Eligible', 'pass': True},
                    {'label': 'State Eligible', 'pass': True},
                    {'label': 'Education Eligible', 'pass': True}
                ],
                'estimated_benefit': '₹75,000',
                'target_occupations': ['Student'],
                'target_sectors': ['Education']
            }
        ]

        created_schemes = {}
        for sdata in schemes_data:
            s_id = sdata['id']
            slug = sdata['slug']
            cat = sdata.get('category', 'Social')
            cat_prefix = (cat[:3].upper()) if cat else 'GEN'
            if len(cat_prefix) < 3: cat_prefix = cat_prefix.ljust(3, 'X')
            default_code = f"SCH-{cat_prefix}-{s_id:04d}"

            obj, created = Scheme.objects.get_or_create(
                id=s_id,
                defaults={
                    'scheme_code': default_code,
                    'slug': slug,
                    'name': sdata['name'],
                    'ministry': sdata['ministry'],
                    'category': sdata['category'],
                    'gov_level': sdata['gov_level'],
                    'state_coverage': sdata['state_coverage'],
                    'description': sdata['desc'],
                    'objective': sdata['desc'],
                    'benefits_summary': sdata['benefits_summary'],
                    'benefits': sdata['benefits'],
                    'eligibility': sdata['eligibility'],
                    'documents': sdata['documents'],
                    'process': sdata['process'],
                    'deadline': sdata['deadline'],
                    'ai_score': sdata['ai_score'],
                    'ai_checklist': sdata['ai_checklist'],
                    'estimated_benefit': sdata['estimated_benefit'],
                    'target_occupations': sdata.get('target_occupations', []),
                    'target_sectors': sdata.get('target_sectors', []),
                    'is_active': True
                }
            )
            if not obj.scheme_code:
                obj.scheme_code = default_code
                obj.save(update_fields=['scheme_code'])
            created_schemes[s_id] = obj

        # 3. Documents for Chetan
        UserDocument.objects.get_or_create(
            user=chetan,
            doc_key='Identity',
            defaults={
                'doc_type_name': 'Voter ID Card',
                'category': 'mandatory',
                'file_name': 'Voter_ID_Card_Front_Back.pdf',
                'file_size': '1.45 MB',
                'file_format': 'PDF Document',
                'status': 'Verified'
            }
        )
        UserDocument.objects.get_or_create(
            user=chetan,
            doc_key='Income',
            defaults={
                'doc_type_name': 'Income Certificate',
                'category': 'mandatory',
                'file_name': 'Income_Certificate_Tehsildar_2026.pdf',
                'file_size': '1.20 MB',
                'file_format': 'PDF Document',
                'status': 'Verified'
            }
        )
        UserDocument.objects.get_or_create(
            user=chetan,
            doc_key='Address',
            defaults={
                'doc_type_name': 'State Domicile Certificate',
                'category': 'mandatory',
                'file_name': 'Domicile_Certificate_Uttarakhand.png',
                'file_size': '890 KB',
                'file_format': 'Image (PNG)',
                'status': 'Verified'
            }
        )
        UserDocument.objects.get_or_create(
            user=chetan,
            doc_key='Marksheet',
            defaults={
                'doc_type_name': 'Class 12th Marksheet',
                'category': 'academic',
                'file_name': 'Senior_Secondary_Marksheet_12th.pdf',
                'file_size': '2.10 MB',
                'file_format': 'PDF Document',
                'status': 'Verified'
            }
        )
        UserDocument.objects.get_or_create(
            user=chetan,
            doc_key='Other',
            defaults={
                'doc_type_name': 'Land Records (Khasra/Khatauni)',
                'category': 'other',
                'file_name': 'Land_Holding_Khasra_Records.pdf',
                'file_size': '3.40 MB',
                'file_format': 'PDF Document',
                'status': 'Under Review'
            }
        )

        # 4. Applications for Chetan
        apps = [
            {'scheme_id': 1, 'app_id': 'PMK-2026-00451', 'status': 'approved', 'stage': 4, 'name': 'PM-KISAN Samman Nidhi'},
            {'scheme_id': 2, 'app_id': 'NMMS-2026-00877', 'status': 'review', 'stage': 2, 'name': 'National Means-cum-Merit Scholarship'},
            {'scheme_id': 3, 'app_id': 'SUI-2026-00129', 'status': 'rejected', 'stage': 1, 'name': 'Stand-Up India Scheme', 'reason': 'Business plan did not meet the minimum project viability threshold. You may reapply with updated financials.'},
            {'scheme_id': 4, 'app_id': 'ABY-2026-00902', 'status': 'approved', 'stage': 4, 'name': 'Ayushman Bharat — PM-JAY'},
            {'scheme_id': 5, 'app_id': 'PMY-2026-00344', 'status': 'review', 'stage': 2, 'name': 'Pradhan Mantri Awas Yojana'},
            {'scheme_id': 6, 'app_id': 'SSY-2026-00560', 'status': 'approved', 'stage': 3, 'name': 'Sukanya Samriddhi Yojana'},
            {'scheme_id': 7, 'app_id': 'APY-2026-00718', 'status': 'submitted', 'stage': 0, 'name': 'Atal Pension Yojana'},
            {'scheme_id': 8, 'app_id': 'NAPS-2026-00095', 'status': 'rejected', 'stage': 2, 'name': 'National Apprenticeship Promotion Scheme', 'reason': 'Establishment withdrew the apprenticeship offer before final approval. You can apply to a different establishment.'}
        ]

        for a in apps:
            Application.objects.get_or_create(
                application_id=a['app_id'],
                defaults={
                    'user': chetan,
                    'scheme': created_schemes.get(a['scheme_id']),
                    'scheme_name': a['name'],
                    'status': a['status'],
                    'stage': a['stage'],
                    'rejection_reason': a.get('reason')
                }
            )

        # 5. Bookmarks
        if 1 in created_schemes:
            SchemeBookmark.objects.get_or_create(user=chetan, scheme=created_schemes[1])
        if 4 in created_schemes:
            SchemeBookmark.objects.get_or_create(user=chetan, scheme=created_schemes[4])

        # 6. Admin updates
        if 1 in created_schemes:
            SchemeUpdate.objects.get_or_create(
                scheme=created_schemes[1],
                ministry_or_node='Ministry of Agriculture & Farmers Welfare',
                defaults={
                    'change_summary': 'Updated exclusion criteria for institutional landowners & updated e-KYC deadline.',
                    'status': 'pending'
                }
            )
        if 2 in created_schemes:
            SchemeUpdate.objects.get_or_create(
                scheme=created_schemes[2],
                ministry_or_node='Department of School Education & Literacy',
                defaults={
                    'change_summary': 'Revised family income limit from ₹3.0L to ₹3.5L per annum for NMMSS.',
                    'status': 'approved'
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded CHORD database.'))

if __name__ == '__main__':
    from django.core.management import call_command
    call_command('seed_data')
