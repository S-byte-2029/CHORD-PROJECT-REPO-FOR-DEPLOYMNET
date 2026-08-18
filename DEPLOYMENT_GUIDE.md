# CHORD Platform — Complete Production Deployment Guide

This guide provides end-to-end instructions for deploying the **CHORD (Citizen Welfare & Scheme Delivery Platform)** monorepo across:
- **Frontend**: Vercel *(or Netlify)*
- **Backend**: Render *(or Railway)*
- **Database**: Supabase (Managed PostgreSQL)
- **Version Control & CI/CD**: GitHub

---

## 1. Repository Structure & Folder Boundaries

Your GitHub repository should follow this clean monorepo layout:

```
CHORD Workspace /
├── .gitignore                   # Root ignore for secrets, node_modules, build & python artifacts
├── DEPLOYMENT_GUIDE.md          # Complete deployment documentation
├── .env.example                 # Root environment reference
│
├── frontend/                    # All Client-Side Assets (Vercel / Netlify)
│   ├── vercel.json              # Vercel SPA routes, build command & headers
│   ├── netlify.toml             # Netlify build command & redirects
│   ├── _redirects               # Clean URL & SPA routing rules
│   ├── package.json             # Build script (`npm run build`)
│   ├── env-config.js            # Runtime dynamic API URL injector
│   ├── api.js                   # Central REST API Client
│   ├── index.html               # Canonical Root Entrypoint
│   ├── land.html, search.html, login.html, dashboard.html, etc.
│   └── .env.example
│
└── backend/                     # All Server-Side Django Assets (Render / Railway)
    ├── render.yaml              # Render Blueprint Infrastructure-as-Code
    ├── Procfile                 # Process runner
    ├── requirements.txt         # Django, dj-database-url, psycopg2, gunicorn, whitenoise
    ├── manage.py
    ├── chord_backend/
    │   ├── settings.py          # PostgreSQL pooler, dynamic CORS, ALLOWED_HOSTS
    │   ├── urls.py
    │   └── wsgi.py
    ├── api/
    │   ├── middleware.py        # Dynamic CORS middleware (supports *.vercel.app)
    │   ├── models.py, views.py, urls.py
    │   └── management/commands/seed_data.py
    ├── scripts/
    │   ├── migrate_and_seed.py  # Live Supabase schema initializer & seeder
    │   └── smoke_test.py        # End-to-end automated smoke test suite
    └── .gitignore
```

---

## 2. Step 1: Push Repository to GitHub

Run these commands inside your project root:

```bash
# 1. Initialize git (if not already initialized)
git init

# 2. Stage all files
git add .

# 3. Commit clean monorepo
git commit -m "feat: complete monorepo setup for Vercel, Render, and Supabase"

# 4. Set main branch
git branch -M main

# 5. Link to your GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git

# 6. Push to GitHub
git push -u origin main
```

---

## 3. Step 2: Supabase Managed PostgreSQL Database

1. Log into [supabase.com](https://supabase.com) and create a project (e.g. `chord-db`).
2. Go to **Project Settings** → **Database** → **Connection String**.
3. Select **URI** (or **Session Pooler**) and copy the connection string:
   ```
   postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
   *(Ensure you replace `[YOUR_PASSWORD]` with your database password and keep `?sslmode=require`)*.

---

## 4. Step 3: Deploy Backend on Render

1. Log into [render.com](https://render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the Web Service settings:
   - **Name**: `chord-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python api/management/commands/seed_data.py
     ```
   - **Start Command**:
     ```bash
     gunicorn chord_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
     ```
4. In the **Environment Variables** section, add:

| Key | Recommended Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require` | Supabase URI |
| `SECRET_KEY` | *(Generate a 50+ character random string)* | Django Security Key |
| `DEBUG` | `False` | Production safety |
| `ALLOWED_HOSTS` | `.onrender.com,localhost,127.0.0.1` | Permits Render domains |
| `CORS_ALLOWED_ORIGINS` | `https://*.vercel.app,http://localhost:3000` | Whitelists Vercel apps |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com,https://*.vercel.app` | CSRF protection |
| `PYTHONUNBUFFERED` | `1` | Real-time console logs |

5. Click **Create Web Service**. Render will build the image, run migrations, seed initial schemes, and assign a live URL (e.g. `https://chord-backend.onrender.com`).

---

## 5. Step 4: Deploy Frontend on Vercel

1. Log into [vercel.com](https://vercel.com) and click **Add New...** → **Project**.
2. Select your GitHub repository.
3. Configure Project Settings:
   - **Root Directory**: Click *Edit* and select `frontend`.
   - **Framework Preset**: `Other`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.`
4. In **Environment Variables**, add:

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://chord-backend.onrender.com/api` |
| `CHORD_API_URL` | `https://chord-backend.onrender.com/api` |

*(Replace with your actual Render backend URL ending in `/api`)*.

5. Click **Deploy**. Vercel will build the frontend, inject your API URL, and provide a production link (e.g. `https://chord-welfare.vercel.app`).

---

## 6. Step 5: Live Smoke Test Verification

Run the automated test suite against your live Render backend:

```bash
# Test live Render API endpoint:
python3 backend/scripts/smoke_test.py https://chord-backend.onrender.com/api
```

### Manual Verification Checklist:

| Test Target | URL / Action | Expected Result |
| :--- | :--- | :--- |
| **Landing Page** | `https://chord-welfare.vercel.app/` | Hero section, analytics charts, and live feed render seamlessly |
| **Scheme Directory** | `https://chord-welfare.vercel.app/search` | Schemes fetch dynamically from Supabase via Render API |
| **Citizen Login** | Login with `chetan.rawat@example.com` / `password123` (OTP: `123456`) | OTP verification succeeds, JWT token issued, redirect to dashboard |
| **Welfare Twin** | Visit `https://chord-welfare.vercel.app/profile` | Profile completeness meter calculates and updates in real-time |
| **Applications** | Apply for any scheme in scheme details | New application created and visible under `/track-applications` |
| **Admin Panel** | Login with `admin.officer@gov.in` / `admin123` | Real-time stats, scheme manager, and citizen audit dashboard load |
