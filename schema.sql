-- ============================================================================
-- CHORD PLATFORM — SUPABASE / POSTGRESQL PRODUCTION DATABASE SCHEMA
-- Multi-Tenant Welfare Delivery, Scheme Management & Verification Architecture
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. CITIZEN PROFILES / USER ACCOUNTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_useraccount (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30) DEFAULT '',
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'citizen' CHECK (role IN ('citizen', 'admin', 'verifier')),
    token VARCHAR(64) DEFAULT '',
    
    -- OTP Authentication
    otp_code VARCHAR(10) DEFAULT '123456',
    otp_created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Demographics & Welfare Twin Parameters
    dob VARCHAR(30) DEFAULT '',
    gender VARCHAR(20) DEFAULT 'Male',
    state VARCHAR(100) DEFAULT '',
    district VARCHAR(100) DEFAULT '',
    address TEXT DEFAULT '',
    
    -- Occupation, Income & Social Category
    occupation VARCHAR(50) DEFAULT 'General',
    income INTEGER DEFAULT 0,
    education VARCHAR(50) DEFAULT 'General',
    category VARCHAR(30) DEFAULT 'General',
    
    -- Disability & Alerts
    has_disability BOOLEAN DEFAULT FALSE,
    disability_type VARCHAR(100) DEFAULT '',
    disability_pct INTEGER DEFAULT 0,
    email_alerts BOOLEAN DEFAULT TRUE,
    sms_alerts BOOLEAN DEFAULT TRUE,
    share_profile BOOLEAN DEFAULT FALSE,
    
    avatar VARCHAR(255) NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_useraccount_email ON api_useraccount(email);
CREATE INDEX IF NOT EXISTS idx_useraccount_token ON api_useraccount(token);
CREATE INDEX IF NOT EXISTS idx_useraccount_role ON api_useraccount(role);

-- ----------------------------------------------------------------------------
-- 2. SCHEMES & ENTITLEMENTS CATALOG
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_scheme (
    id BIGSERIAL PRIMARY KEY,
    scheme_code VARCHAR(50) UNIQUE,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) DEFAULT 'Social Welfare',
    ministry VARCHAR(255) DEFAULT 'Government of India',
    gov_level VARCHAR(50) DEFAULT 'Central Government',
    state_coverage VARCHAR(100) DEFAULT 'All India',
    status VARCHAR(50) DEFAULT 'Applications Open',
    
    -- Objective & Content
    objective TEXT DEFAULT '',
    description TEXT DEFAULT '',
    beneficiaries TEXT DEFAULT '',
    
    -- Structured JSON Data
    benefits_summary VARCHAR(255) DEFAULT '',
    benefits JSONB DEFAULT '[]'::jsonb,
    eligibility JSONB DEFAULT '[]'::jsonb,
    documents JSONB DEFAULT '[]'::jsonb,
    process JSONB DEFAULT '[]'::jsonb,
    
    -- Application & Deadlines
    deadline VARCHAR(100) DEFAULT 'Ongoing',
    official_link VARCHAR(255) DEFAULT '#',
    contact_info JSONB DEFAULT '{}'::jsonb,
    faqs JSONB DEFAULT '[]'::jsonb,
    
    -- AI Scoring & Matching Metadata
    ai_score INTEGER DEFAULT 90,
    ai_checklist JSONB DEFAULT '[]'::jsonb,
    estimated_benefit VARCHAR(100) DEFAULT 'Direct Benefit Transfer',
    target_occupations JSONB DEFAULT '[]'::jsonb,
    target_sectors JSONB DEFAULT '[]'::jsonb,
    max_income INTEGER DEFAULT 1200000,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheme_code ON api_scheme(scheme_code);
CREATE INDEX IF NOT EXISTS idx_scheme_slug ON api_scheme(slug);
CREATE INDEX IF NOT EXISTS idx_scheme_category ON api_scheme(category);
CREATE INDEX IF NOT EXISTS idx_scheme_state ON api_scheme(state_coverage);

-- ----------------------------------------------------------------------------
-- 3. AUTOMATED UNIQUE SCHEME ID GENERATOR TRIGGER
-- Format: SCH-<CATEGORY_CODE_3>-<RANDOM_ALPHANUMERIC_6> (e.g. SCH-EDU-9X82A1, SCH-AGR-44B1C0)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_scheme_id()
RETURNS TRIGGER AS $$
DECLARE
    cat_prefix VARCHAR(3);
    rand_suffix VARCHAR(6);
    candidate_code VARCHAR(50);
BEGIN
    -- If scheme_code is already provided, keep it
    IF NEW.scheme_code IS NOT NULL AND NEW.scheme_code != '' THEN
        RETURN NEW;
    END IF;

    -- Extract first 3 letters of category, fallback to 'GEN'
    cat_prefix := UPPER(SUBSTRING(COALESCE(NEW.category, 'GEN') FROM 1 FOR 3));
    IF LENGTH(cat_prefix) < 3 THEN
        cat_prefix := RPAD(cat_prefix, 3, 'X');
    END IF;

    -- Generate 6 uppercase alphanumeric characters from MD5 hash
    rand_suffix := UPPER(SUBSTRING(MD5(RANDOM()::TEXT || CLOCK_TIMESTAMP()::TEXT) FROM 1 FOR 6));
    candidate_code := 'SCH-' || cat_prefix || '-' || rand_suffix;

    -- Ensure uniqueness in api_scheme
    WHILE EXISTS (SELECT 1 FROM api_scheme WHERE scheme_code = candidate_code) LOOP
        rand_suffix := UPPER(SUBSTRING(MD5(RANDOM()::TEXT || CLOCK_TIMESTAMP()::TEXT) FROM 1 FOR 6));
        candidate_code := 'SCH-' || cat_prefix || '-' || rand_suffix;
    END LOOP;

    NEW.scheme_code := candidate_code;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_scheme_id_trigger ON api_scheme;
CREATE TRIGGER set_scheme_id_trigger
BEFORE INSERT ON api_scheme
FOR EACH ROW
EXECUTE FUNCTION generate_scheme_id();

-- ----------------------------------------------------------------------------
-- 4. ONE-TIME BACKFILL: ASSIGN SCHEME CODES TO EXISTING RECORDS
-- ----------------------------------------------------------------------------
UPDATE api_scheme
SET scheme_code = 'SCH-' || 
    UPPER(RPAD(SUBSTRING(COALESCE(category, 'GEN') FROM 1 FOR 3), 3, 'X')) || 
    '-' || 
    UPPER(SUBSTRING(MD5(id::TEXT || name || RANDOM()::TEXT) FROM 1 FOR 6))
WHERE scheme_code IS NULL OR scheme_code = '';

-- ----------------------------------------------------------------------------
-- 5. CITIZEN DOCUMENT LOCKER TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_userdocument (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES api_useraccount(id) ON DELETE CASCADE,
    doc_key VARCHAR(50) DEFAULT 'Identity',
    doc_type_name VARCHAR(150) DEFAULT 'Government Document',
    category VARCHAR(50) DEFAULT 'mandatory' CHECK (category IN ('mandatory', 'academic', 'other')),
    file VARCHAR(255) NULL,
    file_name VARCHAR(255) DEFAULT 'document.pdf',
    file_size VARCHAR(50) DEFAULT '1.2 MB',
    file_format VARCHAR(50) DEFAULT 'PDF Document',
    status VARCHAR(50) DEFAULT 'Verified' CHECK (status IN ('Verified', 'Under Review', 'Pending', 'Rejected', 'Reupload')),
    admin_notes TEXT DEFAULT '',
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_userdocument_user ON api_userdocument(user_id);
CREATE INDEX IF NOT EXISTS idx_userdocument_dockey ON api_userdocument(doc_key);

-- ----------------------------------------------------------------------------
-- 6. SCHEME APPLICATIONS & LIFECYCLE TRACKING TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_application (
    id BIGSERIAL PRIMARY KEY,
    application_id VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT REFERENCES api_useraccount(id) ON DELETE CASCADE,
    scheme_id BIGINT REFERENCES api_scheme(id) ON DELETE SET NULL,
    scheme_name VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'submitted' CHECK (status IN ('submitted', 'review', 'approved', 'rejected')),
    stage INTEGER DEFAULT 0 CHECK (stage >= 0 AND stage <= 4),
    rejection_reason TEXT NULL,
    applicant_data JSONB DEFAULT '{}'::jsonb,
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_application_id ON api_application(application_id);
CREATE INDEX IF NOT EXISTS idx_application_user ON api_application(user_id);
CREATE INDEX IF NOT EXISTS idx_application_status ON api_application(status);

-- ----------------------------------------------------------------------------
-- 7. BOOKMARKS, FEEDBACK & REPORTING TABLES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_schemebookmark (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES api_useraccount(id) ON DELETE CASCADE,
    scheme_id BIGINT REFERENCES api_scheme(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, scheme_id)
);

CREATE TABLE IF NOT EXISTS api_schemefeedback (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT REFERENCES api_scheme(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES api_useraccount(id) ON DELETE SET NULL,
    rating INTEGER DEFAULT 5 CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_schemereport (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT REFERENCES api_scheme(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES api_useraccount(id) ON DELETE SET NULL,
    issues JSONB DEFAULT '[]'::jsonb,
    details TEXT DEFAULT '',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_contactmessage (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_schemeupdate (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT REFERENCES api_scheme(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    summary TEXT DEFAULT '',
    details TEXT DEFAULT '',
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    source_url VARCHAR(255) DEFAULT '',
    submitted_by VARCHAR(150) DEFAULT 'Ministry Portal Sync',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
