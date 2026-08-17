# CHORD Platform — Complete Production Deployment Guide

This guide provides end-to-end instructions for deploying the decoupled **CHORD (Citizen Welfare & Scheme Delivery Platform)** across:
- **Frontend**: Netlify (Edge CDN + SPA Routing)
- **Backend**: Railway (Django 6 REST API + Gunicorn + WhiteNoise)
- **Database**: Supabase (Managed PostgreSQL with Connection Pooling)
- **Version Control & CI/CD**: GitHub

---

## 1. Project Architecture & Decoupled Boundaries

```
CHORD Workspace /
├── .gitignore               # Root ignore for secrets, node_modules, build & python artifacts
├── netlify.toml             # Netlify build command, headers, and SPA redirects
├── _redirects               # Clean URL & SPA routing rules (/* /index.html 200)
├── package.json             # Frontend build scripts (npm run build, npm start)
├── .env.example             # Frontend environment template (VITE_API_URL)
├── env-config.js            # Runtime dynamic environment injector
├── index.html               # Main canonical landing entrypoint
├── land.html, search.html, login.html, dashboard.html, etc.
├── api.js                   # Decoupled Central API Client
│
└── backend/
    ├── .gitignore           # Backend ignore (db.sqlite3, .env, staticfiles, etc.)
    ├── .env.example         # Backend environment template
    ├── requirements.txt     # Django, dj-database-url, psycopg2, gunicorn, whitenoise
    ├── Procfile             # Railway web process declaration
    ├── railway.json         # Railway build and deploy specification
    ├── nixpacks.toml        # Railway Nixpacks builder configuration
    ├── manage.py
    ├── chord_backend/
    │   ├── settings.py      # Supabase PostgreSQL, dynamic PORT/ALLOWED_HOSTS/CORS
    │   ├── urls.py
    │   └── wsgi.py
    ├── api/
    │   ├── middleware.py    # Production CORS middleware with Netlify regex support
    │   ├── models.py, views.py, urls.py
    │   └── management/commands/seed_data.py
    └── scripts/
        ├── migrate_and_seed.py # Live Supabase schema initializer & seeder
        └── smoke_test.py       # End-to-end smoke test suite
```

---

## 2. Step 1: Push Repository to GitHub

Open your terminal in the project directory and run:

```bash
# 1. Initialize git repository if not already initialized
git init

# 2. Add all files (respecting .gitignore)
git add .

# 3. Commit the decoupled codebase
git commit -m "chore: decouple frontend and backend for Netlify, Railway, and Supabase deployment"

# 4. Set default branch to main
git branch -M main

# 5. Link your GitHub remote repository (replace with your GitHub repo URL)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git

# 6. Push to GitHub
git push -u origin main
```

---

## 3. Step 2: Set Up Supabase Managed PostgreSQL

1. Log into [supabase.com](https://supabase.com) and create a new project (e.g. `chord-production-db`).
2. Go to **Project Settings** → **Database** → **Connection String**.
3. Select **URI** (or **Session Pooler**) and copy the PostgreSQL URI:
   ```
   postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
   *(Ensure you replace `[YOUR_PASSWORD]` with your real database password and keep `?sslmode=require`)*.

---

## 4. Step 3: Deploy Backend on Railway

1. Log into [railway.app](https://railway.app) and click **New Project** → **Deploy from GitHub repo**.
2. Select your repository.
3. In Railway **Settings**:
   - Set **Root Directory** to `/backend` (or leave as root with Procfile).
4. In Railway **Variables** tab, add the following environment variables:

| Variable | Recommended Value | Notes |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Generate a 50+ character random string)* | Required by Django |
| `DEBUG` | `False` | Production safety |
| `ALLOWED_HOSTS` | `*.railway.app,*.up.railway.app,localhost,127.0.0.1` | Permits Railway domains |
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require` | Your Supabase URI |
| `CORS_ALLOW_ALL_ORIGINS` | `False` | Strict mode |
| `CORS_ALLOWED_ORIGINS` | `https://*.netlify.app,http://localhost:3000` | Netlify domain |
| `CSRF_TRUSTED_ORIGINS` | `https://*.netlify.app,https://*.railway.app,https://*.up.railway.app` | CSRF protection |
| `PYTHONUNBUFFERED` | `1` | Real-time console logs |

5. Under **Settings** → **Networking**, click **Generate Domain** (e.g., `https://chord-backend-production.up.railway.app`).
6. Railway will automatically build and deploy. Once deployed, Railway executes migrations and seeds the database automatically using `railway.json`.

---

## 5. Step 4: Deploy Frontend on Netlify

1. Log into [netlify.com](https://netlify.com) and click **Add new site** → **Import an existing project**.
2. Connect to **GitHub** and choose your repository.
3. Configure Build Settings:
   - **Base directory**: `/` (Leave empty/root)
   - **Build command**: `npm run build`
   - **Publish directory**: `.`
4. In **Site configuration** → **Environment variables**, add:

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://chord-backend-production.up.railway.app/api` |
| `CHORD_API_URL` | `https://chord-backend-production.up.railway.app/api` |

*(Replace with your actual Railway backend domain, ensuring it ends with `/api`)*.

5. Click **Deploy Site**.
6. Once deployed, update `CORS_ALLOWED_ORIGINS` in Railway with your exact Netlify domain (e.g., `https://chord-portal.netlify.app`).

---

## 6. Step 5: Initialize Schema & Seed Supabase (If Needed Manually)

If you wish to run migrations directly from your terminal against the Supabase database:

```bash
# Set your DATABASE_URL in your terminal session
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require"

# Run the automated migration and seeder
python3 backend/scripts/migrate_and_seed.py
```

---

## 7. Step 6: Live Smoke Testing & Verification

Run the automated smoke test against your live deployed Railway backend:

```bash
# Run smoke test against live production URL:
python3 backend/scripts/smoke_test.py https://chord-backend-production.up.railway.app/api
```

### Manual Verification Checklist

| Flow / Feature | Test Procedure | Expected Result |
| :--- | :--- | :--- |
| **Landing Page** | Visit `https://your-site.netlify.app/` | Hero section, analytics charts, and live feed render without 404s |
| **Scheme Search** | Visit `/search` and filter by "Agriculture" or "Education" | Schemes load dynamically from Supabase via Railway REST API |
| **Citizen Auth** | Log in with `chetan.rawat@example.com` / `password123` (OTP: `123456`) | OTP verification succeeds, JWT token stored, redirected to dashboard |
| **Welfare Twin** | Check `/profile` completeness meter and edit profile details | Data persists across page reloads in Supabase PostgreSQL |
| **Document Vault** | Upload or view files in `/document-upload` | Document badges update and persist |
| **Applications** | Apply for a scheme in `/scheme-details` or `/dashboard` | New application ID generated and visible in `/track-applications` |
| **Admin Panel** | Log in with `admin.officer@gov.in` / `admin123` | Real-time statistics, scheme manager, and beneficiary audit load |
