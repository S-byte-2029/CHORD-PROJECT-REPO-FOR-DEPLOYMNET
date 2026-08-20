#!/usr/bin/env python3
"""
CHORD Platform — 500 National Welfare Schemes Enricher & Ingestion Script
Enriches CSV dataset with all required database fields for `api_scheme` / `Scheme` model
and ingests all 500 records into Supabase PostgreSQL in 100-record chunks.
Also outputs an SQL insert file `backend/data/national_schemes_500.sql`.
"""

import os
import sys
import csv
import json
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chord_backend.settings')

import django
django.setup()

from api.models import Scheme
from django.db import transaction

CSV_PATH = BASE_DIR / 'data' / 'national_schemes_500.csv'
SQL_OUT_PATH = BASE_DIR / 'data' / 'national_schemes_500.sql'

CATEGORY_META = {
    'MSME': {
        'prefix': 'MSM',
        'occupations': ['Business Owner', 'Self Employed', 'General'],
        'documents': ['Aadhaar Card', 'Udyam Registration Certificate', 'PAN Card', 'Bank Account Statement (6 Months)', 'Business Project Report'],
        'beneficiaries': 'Micro, Small, and Medium Enterprise owners, artisans, and emerging entrepreneurs.',
        'benefit_est': '₹5,00,000 – ₹25,00,000 Credit & Grant Support',
        'max_income': 2500000,
        'eligibility': [
            'Registered micro, small, or medium enterprise in eligible sector.',
            'Applicant must hold valid Udyam registration & PAN card.',
            'Resident citizen of the designated state/UT or All India.',
            'No existing default record with formal financial institutions.'
        ]
    },
    'Finance': {
        'prefix': 'FIN',
        'occupations': ['Salaried Employee', 'Business Owner', 'Daily Wage Worker', 'General'],
        'documents': ['Aadhaar Card', 'PAN Card', 'Income Certificate', 'Bank Passbook / Cancelled Cheque', 'Address Proof'],
        'beneficiaries': 'Low-to-middle income households, unbanked citizens, and micro-investors.',
        'benefit_est': '₹50,000 – ₹2,00,000 Financial Grant / Subsidy',
        'max_income': 800000,
        'eligibility': [
            'Indian citizen residing in the specified state coverage area.',
            'Annual family income within prescribed welfare limits.',
            'Active bank account linked with Aadhaar for DBT transfer.',
            'Valid identity and domicile verification documentation.'
        ]
    },
    'Education': {
        'prefix': 'EDU',
        'occupations': ['Student', 'General'],
        'documents': ['Aadhaar Card', 'Previous Class Marksheet', 'Bonafide Student Certificate', 'Income Certificate', 'Bank Account Passbook'],
        'beneficiaries': 'Students enrolled in school, college, vocational, or higher education institutions.',
        'benefit_est': '₹12,000 – ₹75,000 / year Scholarship',
        'max_income': 450000,
        'eligibility': [
            'Enrolled as a regular student in a recognized educational institution.',
            'Minimum 50% aggregate marks in preceding qualifying examination.',
            'Family annual income below ₹4.5 Lakh from all sources.',
            'Applicable for students in designated state or All India.'
        ]
    },
    'Health': {
        'prefix': 'HEA',
        'occupations': ['Daily Wage Worker', 'Farmer', 'Unemployed', 'General', 'Salaried Employee'],
        'documents': ['Aadhaar Card', 'Ration Card / BPL Card', 'Income Certificate', 'Bank Account Details', 'Disability / Medical Certificate (if applicable)'],
        'beneficiaries': 'Vulnerable families, senior citizens, women, and unorganised sector workers needing healthcare coverage.',
        'benefit_est': '₹1,00,000 – ₹5,00,000 Cashless Health Cover / year',
        'max_income': 600000,
        'eligibility': [
            'Citizen household residing in the covered state or All India.',
            'Family classified under priority/deprivation categories or low-income threshold.',
            'Aadhaar seeded with public distribution / health registry.',
            'No existing comprehensive corporate healthcare coverage.'
        ]
    },
    'Agriculture': {
        'prefix': 'AGR',
        'occupations': ['Farmer', 'Daily Wage Worker', 'General'],
        'documents': ['Aadhaar Card', 'Land Ownership Record (Khata/Khasra/ROR)', 'Bank Account Passbook', 'Mobile Number', 'Sowing / Crop Certificate'],
        'beneficiaries': 'Small, marginal, and tenant farmers and agricultural laborers.',
        'benefit_est': '₹6,000 – ₹25,000 Direct Income & Equipment Subsidy',
        'max_income': 600000,
        'eligibility': [
            'Small, marginal, or tenant farmer with cultivable landholding or agricultural labor record.',
            'Resident farmer in the designated state / UT or All India.',
            'Aadhaar-linked active bank account for direct benefit transfer.',
            'Non-taxpayer status under agricultural income guidelines.'
        ]
    }
}

STANDARD_PROCESS = [
    {"title": "Online Registration", "desc": "Register on the official portal with Aadhaar and mobile verification."},
    {"title": "Application Filing", "desc": "Fill the electronic form and upload required supporting credentials."},
    {"title": "Departmental Scrutiny", "desc": "State and central welfare officers verify submitted details and eligibility."},
    {"title": "Sanction & Approval", "desc": "Digital approval letter issued upon successful scrutiny."},
    {"title": "Direct Benefit Transfer", "desc": "Sanctioned grant or subsidy credited directly to beneficiary bank account via DBT."}
]

def enrich_scheme_record(row, index):
    name = row['name'].strip()
    category = row['category'].strip()
    ministry = row['ministry'].strip()
    state_coverage = row['state_coverage'].strip()
    benefits_summary = row['benefits_summary'].strip()
    description = row['description'].strip()

    meta = CATEGORY_META.get(category, CATEGORY_META['Finance'])
    prefix = meta['prefix']
    rand_hex = uuid.uuid4().hex[:6].upper()
    scheme_code = f"SCH-{prefix}-{rand_hex}"

    slug = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('/', '-')
    gov_level = 'Central Government' if state_coverage == 'All India' else 'State Government'
    objective = f"Empower eligible beneficiaries in {state_coverage} under {category} with structured financial grants, institutional support, and sector incentives."
    
    benefits = [
        {"title": "Direct Financial Assistance", "desc": benefits_summary, "icon": "rupee"},
        {"title": "Sector Development Incentives", "desc": "Structured support, skill training, and capacity-building resources.", "icon": "award"},
        {"title": "Direct Bank Disbursal", "desc": "100% electronic transfer directly via Aadhaar-seeded bank account.", "icon": "shield"}
    ]

    eligibility = meta['eligibility']
    documents = meta['documents']
    beneficiaries = meta['beneficiaries']
    estimated_benefit = meta['benefit_est']
    target_occupations = meta['occupations']
    target_sectors = [category, 'Social Welfare', 'General']
    max_income = meta['max_income']
    ai_score = 90 + (index % 9)

    ai_checklist = [
        {"label": "Income Criteria Matched", "pass": True},
        {"label": "State / UT Domicile Verified", "pass": True},
        {"label": "Sector Eligibility Confirmed", "pass": True},
        {"label": "Identity Credentials Ready", "pass": True}
    ]

    faqs = [
        {"q": f"Who is eligible for {name}?", "a": f"Citizens residing in {state_coverage} matching the {category} category parameters and income thresholds are eligible to apply."},
        {"q": "How is the benefit amount disbursed?", "a": "All financial grants and subsidies are credited directly into your verified bank account via Direct Benefit Transfer (DBT)."},
        {"q": "What documents are required?", "a": f"Key documents include {', '.join(documents[:3])}."}
    ]

    return {
        'scheme_code': scheme_code,
        'slug': slug,
        'name': name,
        'category': category,
        'ministry': ministry,
        'gov_level': gov_level,
        'state_coverage': state_coverage,
        'status': 'Applications Open',
        'objective': objective,
        'description': description,
        'beneficiaries': beneficiaries,
        'benefits_summary': benefits_summary,
        'benefits': benefits,
        'eligibility': eligibility,
        'documents': documents,
        'process': STANDARD_PROCESS,
        'deadline': '31 Dec 2026',
        'official_link': 'https://www.myscheme.gov.in/',
        'contact_info': {'helpline': '1800-11-0001', 'email': 'support.welfare@gov.in'},
        'faqs': faqs,
        'ai_score': ai_score,
        'ai_checklist': ai_checklist,
        'estimated_benefit': estimated_benefit,
        'target_occupations': target_occupations,
        'target_sectors': target_sectors,
        'max_income': max_income,
        'is_active': True
    }

def main():
    print("=" * 65)
    print("  CHORD Platform — 500 Schemes Enrichment & Ingestion")
    print(f"  Reading: {CSV_PATH}")
    print("=" * 65)

    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found!")
        sys.exit(1)

    records = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            enriched = enrich_scheme_record(row, idx)
            records.append(enriched)

    total = len(records)
    print(f"Loaded and enriched {total} schemes.")

    # 1. Bulk Ingest into Database in 100-record chunks
    batch_size = 100
    created_count = 0
    updated_count = 0

    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        print(f"\nIngesting Batch {(i // batch_size) + 1}/{(total + batch_size - 1) // batch_size} ({len(chunk)} schemes)...")
        with transaction.atomic():
            for rec in chunk:
                obj, created = Scheme.objects.get_or_create(
                    slug=rec['slug'],
                    defaults=rec
                )
                if created:
                    created_count += 1
                else:
                    for k, v in rec.items():
                        setattr(obj, k, v)
                    obj.save()
                    updated_count += 1

    total_in_db = Scheme.objects.count()
    print("\n" + "=" * 65)
    print(f"  INGESTION SUMMARY:")
    print(f"  - Newly Created: {created_count}")
    print(f"  - Updated / Synced: {updated_count}")
    print(f"  - Total Schemes in Database: {total_in_db}")
    print("=" * 65)

    # 2. Also generate standalone SQL script for Supabase SQL Editor
    with open(SQL_OUT_PATH, 'w', encoding='utf-8') as sf:
        sf.write("-- CHORD Platform — 500 National Welfare Schemes Standalone SQL Dump\n")
        sf.write("-- Generated automatically with complete metadata & JSON structures\n\n")
        for r in records:
            b_json = json.dumps(r['benefits']).replace("'", "''")
            e_json = json.dumps(r['eligibility']).replace("'", "''")
            d_json = json.dumps(r['documents']).replace("'", "''")
            p_json = json.dumps(r['process']).replace("'", "''")
            c_json = json.dumps(r['contact_info']).replace("'", "''")
            f_json = json.dumps(r['faqs']).replace("'", "''")
            ac_json = json.dumps(r['ai_checklist']).replace("'", "''")
            to_json = json.dumps(r['target_occupations']).replace("'", "''")
            ts_json = json.dumps(r['target_sectors']).replace("'", "''")

            name_esc = r['name'].replace("'", "''")
            desc_esc = r['description'].replace("'", "''")
            obj_esc = r['objective'].replace("'", "''")
            min_esc = r['ministry'].replace("'", "''")
            bs_esc = r['benefits_summary'].replace("'", "''")
            ben_esc = r['beneficiaries'].replace("'", "''")

            sql = f"""INSERT INTO api_scheme (
    scheme_code, slug, name, category, ministry, gov_level, state_coverage, status,
    objective, description, beneficiaries, benefits_summary, benefits, eligibility,
    documents, process, deadline, official_link, contact_info, faqs, ai_score,
    ai_checklist, estimated_benefit, target_occupations, target_sectors, max_income, is_active
) VALUES (
    '{r['scheme_code']}', '{r['slug']}', '{name_esc}', '{r['category']}', '{min_esc}', '{r['gov_level']}',
    '{r['state_coverage']}', '{r['status']}', '{obj_esc}', '{desc_esc}', '{ben_esc}', '{bs_esc}',
    '{b_json}'::jsonb, '{e_json}'::jsonb, '{d_json}'::jsonb, '{p_json}'::jsonb, '{r['deadline']}',
    '{r['official_link']}', '{c_json}'::jsonb, '{f_json}'::jsonb, {r['ai_score']},
    '{ac_json}'::jsonb, '{r['estimated_benefit']}', '{to_json}'::jsonb, '{ts_json}'::jsonb,
    {r['max_income']}, true
) ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    ministry = EXCLUDED.ministry,
    benefits_summary = EXCLUDED.benefits_summary,
    description = EXCLUDED.description,
    state_coverage = EXCLUDED.state_coverage,
    is_active = true;\n"""
            sf.write(sql)

    print(f"Generated standalone SQL file: {SQL_OUT_PATH} ({SQL_OUT_PATH.stat().st_size // 1024} KB)")

if __name__ == '__main__':
    main()
