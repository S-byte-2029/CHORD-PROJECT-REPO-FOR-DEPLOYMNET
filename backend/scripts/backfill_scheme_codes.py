#!/usr/bin/env python3
"""
CHORD - Scheme Code Automated Backfill Script
Assigns unique SCH-<CATEGORY_CODE>-<RANDOM_6> identifiers to any Scheme
in Supabase / PostgreSQL that does not have a scheme_code.
"""

import os
import sys
import uuid
from pathlib import Path

# Setup Django Environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chord_backend.settings')

import django
django.setup()

from api.models import Scheme

def backfill_scheme_codes():
    schemes = Scheme.objects.all().order_by('id')
    total = schemes.count()
    updated = 0

    print("=" * 60)
    print(f"  CHORD Scheme Code Backfill Automation")
    print(f"  Total Schemes in Database: {total}")
    print("=" * 60)

    for s in schemes:
        if not s.scheme_code:
            cat_prefix = (s.category[:3].upper()) if s.category else 'GEN'
            if len(cat_prefix) < 3:
                cat_prefix = cat_prefix.ljust(3, 'X')
            
            # Generate unique code
            rand_code = uuid.uuid4().hex[:6].upper()
            candidate = f"SCH-{cat_prefix}-{rand_code}"
            
            while Scheme.objects.filter(scheme_code=candidate).exists():
                rand_code = uuid.uuid4().hex[:6].upper()
                candidate = f"SCH-{cat_prefix}-{rand_code}"
            
            s.scheme_code = candidate
            s.save(update_fields=['scheme_code'])
            updated += 1
            print(f" [UPDATED] Scheme ID {s.id}: '{s.name}' -> {s.scheme_code}")
        else:
            print(f" [OK] Scheme ID {s.id}: '{s.name}' -> {s.scheme_code}")

    print("=" * 60)
    print(f"  Backfill Complete! {updated} schemes assigned new scheme codes.")
    print("=" * 60)

if __name__ == '__main__':
    backfill_scheme_codes()
