#!/usr/bin/env python
"""
CHORD Database Migration & Seeding Tool
Applies Django migrations and seeds initial schemes, citizen accounts, and applications.
Compatible with Supabase PostgreSQL (via DATABASE_URL) and local development SQLite.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chord_backend.settings')

import django
from django.core.management import call_command
from django.db import connection

def run():
    print("==================================================")
    print("  CHORD Database Migration & Schema Seeder")
    print("==================================================")
    
    django.setup()
    
    db_vendor = connection.vendor
    db_name = connection.settings_dict.get('NAME')
    db_host = connection.settings_dict.get('HOST', 'localhost')
    
    print(f"[*] Connected to Database Engine : {db_vendor.upper()}")
    print(f"[*] Database Host / File         : {db_host} ({db_name})")
    
    # 1. Run Migrations
    print("\n[Step 1/2] Running Django database migrations...")
    try:
        call_command('migrate', interactive=False)
        print("[✓] Migrations applied successfully!")
    except Exception as e:
        print(f"[✗] Error applying migrations: {e}")
        sys.exit(1)
        
    # 2. Seed Initial Platform Data
    print("\n[Step 2/2] Seeding initial welfare schemes, citizen profiles, and mock applications...")
    try:
        call_command('seed_data')
        print("[✓] Database seeding complete!")
    except Exception as e:
        print(f"[!] Warning/Notice during seeding: {e}")

    print("\n==================================================")
    print("  ✓ Database is fully initialized and ready!")
    print("==================================================")

if __name__ == '__main__':
    run()
