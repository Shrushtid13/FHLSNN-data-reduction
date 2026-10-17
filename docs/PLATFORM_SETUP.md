# Platform Setup Guide

This guide details the exact steps to configure and start the complete platform skeleton (Supabase, Redis, FastAPI, Python Worker, Express API, and React UI).

---

## 1. Supabase Setup

### 1.1 Run Database Migration
1. Open your Supabase project dashboard at [https://supabase.com](https://supabase.com).
2. Navigate to **SQL Editor** in the left sidebar.
3. Open `db/migrations/001_init.sql` from this repository, copy its contents, paste them into the SQL editor, and click **Run**.
4. Verify that tables `datasets`, `experiments`, and `reports` are created and RLS is enabled on all three.

### 1.2 Create Storage Bucket
1. Navigate to **Storage** in the left sidebar.
2. Click **New Bucket**.
3. Name the bucket: `datasets`.
4. Ensure **Public bucket** is **OFF** (it must remain private).
5. Click **Save**.
6. The migration script automatically adds the storage policy allowing authenticated users to read their own uploaded files under `{user_id}/*`.

### 1.3 Create Two Test Users
1. In the Supabase dashboard, navigate to **Authentication** -> **Users**.
2. Click **Add user** -> **Create user**.
3. User A:
   - Email: `user_a@example.com`
   - Password: `Password123!`
   - Auto-confirm: Checked (or click Confirm email).
4. User B:
   - Email: `user_b@example.com`
   - Password: `Password123!`
   - Auto-confirm: Checked.

---

## 2. Environment Variables (.env)

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Fill in the values:
   - `SUPABASE_URL`: Project Settings -> API -> Project URL
   - `SUPABASE_ANON_KEY`: Project Settings -> API -> Project API Keys (`anon` / `public`)
   - `SUPABASE_SERVICE_ROLE_KEY`: Project Settings -> API -> Project API Keys (`service_role` / secret)
   - `REDIS_URL`: `redis://localhost:6379/0`
   - `INTERNAL_API_TOKEN`: A secret string shared between Express and FastAPI (e.g. `secret_token_12345`)
   - `WEB_ORIGIN`: `http://localhost:5173`
   - `PORT`: `4000`
   - `FASTAPI_URL`: `http://localhost:8000`

---

## 3. Start Redis

Run Redis using Docker (or a native Windows service):
```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

---

## 4. Service Start Commands

Open 4 separate PowerShell terminals:

### Terminal 1: FastAPI Service (Port 8000)
```powershell
cd ml_service\service
pip install -r requirements.txt
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Python Background Worker
```powershell
cd ml_service\service
python worker.py
```

### Terminal 3: Express API (Port 4000)
```powershell
cd api
npm install
npm run dev
```

### Terminal 4: React UI (Port 5173)
```powershell
cd web
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser.
