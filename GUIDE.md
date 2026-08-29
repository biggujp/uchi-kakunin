# 🏠 Uchi Kakunin Setsubi — Installation & Usage Guide
# House Inspection System (Complete Guide)

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites](#2-prerequisites)
3. [Google Sheets + Service Account Setup](#3-google-sheets--service-account-setup)
4. [Deploy Backend on Vercel](#4-deploy-backend-on-vercel)
5. [Deploy Frontend on GitHub Pages](#5-deploy-frontend-on-github-pages)
6. [App Configuration & Testing](#6-app-configuration--testing)
7. [Feature-by-Feature Usage Guide](#7-feature-by-feature-usage-guide)
8. [Troubleshooting](#8-troubleshooting)
9. [Environment Variables Reference](#9-environment-variables-reference)

---

## 1. System Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Frontend (HTML)   │────▶│   Backend (Flask)   │────▶│  Google Sheets   │
│   GitHub Pages      │     │   Vercel            │     │  (Database)      │
│                     │     │                     │     │                  │
│  - index.html       │     │  - Auth API         │     │  - Users         │
│  - Tailwind CSS     │     │  - Inspection API   │     │  - Inspections   │
│  - JavaScript       │     │  - Team Sessions    │     │  - TeamSessions  │
│  - Push Notifs      │     │  - Notifications    │     │  - Notifications │
│                     │     │  - Google Sheets    │     │  - CustomItems   │
│                     │     │    integration      │     │  - SharedReports │
└─────────────────────┘     └─────────────────────┘     └──────────────────┘
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | HTML + Tailwind CSS + JavaScript | User interface (Mobile-First) |
| Backend | Python Flask | API + Authentication + Google Sheets |
| Database | Google Sheets | Stores all data |
| FE Hosting | GitHub Pages (free) | Serves HTML files |
| BE Hosting | Vercel (free) | Hosts API |

---

## 2. Prerequisites

### 2.1 Required Accounts
- [ ] **GitHub Account** — for code storage + GitHub Pages
  - Free signup: https://github.com
- [ ] **Google Account** — for Google Sheets + Google Cloud
- [ ] **Vercel Account** — for API hosting
  - Free signup: https://vercel.com (can use GitHub login)

### 2.2 Project Structure
```
uchi-kakunin/
├── index.html              ← Frontend (deployed to GitHub Pages)
├── public/
│   └── index.html          ← Auto-copied for Vercel
├── api/
│   └── index.py            ← Backend API (deployed to Vercel)
├── vercel.json             ← Vercel config
├── requirements.txt        ← Python dependencies
├── README.md
├── INSTALLATION_GUIDE.md   ← Thai guide
└── GUIDE.md                ← English guide (this file)
```

---

## 3. Google Sheets + Service Account Setup

### Step 3.1: Create a Google Spreadsheet

1. Open https://sheets.google.com
2. Click **"+ Blank spreadsheet"**
3. Name it **"Uchi Kakunin Setsubi Database"**
4. Copy the **Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID_HERE]/edit
   ```
   Example: If the URL is `https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit`
   → Spreadsheet ID is `1AbCdEfGhIjKlMnOpQrStUvWxYz`

5. **Save the Spreadsheet ID** — you'll need it for Vercel setup

> 💡 The system will auto-create sheet tabs (Users, InspectionData, TeamSessions, Notifications, SharedReports, CustomChecklistItems) when first used.

### Step 3.2: Create a Google Cloud Project

1. Open https://console.cloud.google.com
2. Select or create a new project:
   - Click "Select a project" in the top-left
   - Click "NEW PROJECT"
   - Name: **Uchi Kakunin Setsubi**
   - Click "CREATE"

### Step 3.3: Enable APIs

1. In Google Cloud Console → Left menu → **APIs & Services** → **Library**
2. Search for **"Google Sheets API"** → Click **"ENABLE"**
3. Search for **"Google Drive API"** → Click **"ENABLE"**

### Step 3.4: Create a Service Account

1. Left menu → **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → Select **"Service Account"**
3. Configure:
   - **Service account name:** `uchi-kakunin-api`
   - **Description:** `API for Uchi Kakunin Setsubi`
   - Click "CREATE AND CONTINUE"
4. (Optional) Select a Role → Click "CONTINUE"
5. Click **"DONE"**

### Step 3.5: Create a Key (JSON)

1. Click on the Service Account you created
2. Go to the **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Select **JSON** → Click **"CREATE"**
5. The JSON file will download automatically → **Keep this file safe!**

### Step 3.6: Grant Spreadsheet Access

1. Open the Google Spreadsheet you created
2. Click **"Share"** in the top-right corner
3. Paste the **Service Account Email** (found in the JSON file, field `client_email`)
   - Example: `uchi-kakunin-api@your-project.iam.gserviceaccount.com`
4. Select Permission: **"Editor"**
5. Click **"Send"**

### Step 3.7: Prepare Service Account JSON

1. Open the downloaded JSON file with a text editor (VS Code, Notepad++)
2. Copy the **entire content** (from `{` to `}`)
3. Save it — you'll use this for the Vercel Environment Variable

> ⚠️ **IMPORTANT:** Never share this file publicly!

---

## 4. Deploy Backend on Vercel

### Step 4.1: Log in to Vercel

1. Open https://vercel.com
2. Click **"Log In"**
3. Select **"Continue with GitHub"**

### Step 4.2: Import Project

1. In Vercel Dashboard → Click **"Add New..."** → **"Project"**
2. Select the **"Import Git Repository"** tab
3. Search for repo `uchi-kakunin` → Click **"Import"**

### Step 4.3: Set Environment Variables

> ⚠️ **CRITICAL:** Set these BEFORE clicking Deploy

In the Project page → Click **"Environment Variables"** tab → Add these:

**Variable 1: GOOGLE_SHEETS_ID** ✅ Required
| Field | Value |
|-------|-------|
| Name | `GOOGLE_SHEETS_ID` |
| Value | `1AbCdEfGhIjKlMnOpQrStUvWxYz` (your Spreadsheet ID) |

**Variable 2: SERVICE_ACCOUNT_JSON** ✅ Required
| Field | Value |
|-------|-------|
| Name | `SERVICE_ACCOUNT_JSON` |
| Value | (paste the entire JSON content) |

> 💡 Copy everything from `{` to `}` in the JSON file

**Variable 3: JWT_SECRET** ❌ Optional
| Field | Value |
|-------|-------|
| Name | `JWT_SECRET` |
| Value | (random string, at least 32 characters) |

> 💡 How to generate: Open terminal and type:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> If not set, the system will auto-derive from Google Sheets ID

### Step 4.4: Deploy

1. After setting up → Click **"Deploy"**
2. Wait 1-2 minutes for the build to complete
3. Click **"Continue to Dashboard"**
4. You'll get a URL like:
   ```
   https://uchi-kakunin.vercel.app
   ```
5. Test the API by opening:
   ```
   https://uchi-kakunin.vercel.app/api
   ```
   If you see `{"status":"ok","message":"House Inspection API",...}` = Success!

### Step 4.5: Redeploy After Code Changes

Every time you push code to the GitHub main branch → Vercel auto-deploys.

To manually redeploy:
1. Vercel Dashboard → Select Project
2. Go to **"Deployments"** tab
3. Click **⋯** → **"Redeploy"**

---

## 5. Deploy Frontend on GitHub Pages

### Step 5.1: Push Files to GitHub

```bash
# In the project folder
git init
git add .
git commit -m "Initial commit - Uchi Kakunin Setsubi"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/uchi-kakunin.git
git push -u origin main
```

### Step 5.2: Enable GitHub Pages

1. Go to the Repository on GitHub
2. Click the **"Settings"** tab
3. Left menu → Select **"Pages"**
4. Source section:
   - Branch: **main**
   - Folder: **/ (root)**
5. Click **"Save"**
6. Wait 1-2 minutes → You'll get a URL like:
   ```
   https://YOUR_USERNAME.github.io/uchi-kakunin/
   ```

---

## 6. App Configuration & Testing

### Step 6.1: Set API URL

1. Open the GitHub Pages URL
2. Click the 👤 icon (top-right) → Click **"Settings"**
3. **API Base URL (Vercel):** Enter your Vercel URL + `/api`
   ```
   https://uchi-kakunin.vercel.app/api
   ```
4. Click **"Save Settings"**

### Step 6.2: Test Connection

1. In the Settings page → Click **"🔍 Test Google Sheets Connection"**
2. Results:
   - ✅ **Connected successfully!** → Ready to use
   - ❌ **Connection failed** → Check Environment Variables

### Step 6.3: Register the First Admin

1. Click 👤 icon → **"Login / Register"**
2. Click **"Register"** link
3. Fill in:
   - **Username:** `admin`
   - **Display Name:** `Administrator`
   - **Password:** (set a password)
4. Click **"Register"**

> 💡 **To make Admin:** Open Google Sheets → "Users" tab → Change Role from `inspector` to `admin`

### Step 6.4: Test Usage

**Test first inspection:**
1. Tap the 🔍 "Inspect" tab
2. Fill property info (owner name + address)
3. Take a photo of the house front
4. Select category → Tap "Pass" or "Issue Found"
5. Click **"Save Report"** at the bottom
6. View report + Export PDF

**Test Multi-User:**
1. Log out
2. Register a new user
3. Login with the new account
4. Try a new inspection

**Test Team Mode:**
1. Login with an Admin account
2. Toggle ☑️ "Team Inspection Mode"
3. Select team members
4. Click "Start Team Sync"
5. Members use the team code to join

### Step 6.5: Verify Google Sheets

Open the Google Spreadsheet to see tabs:
| Tab | Data |
|-----|------|
| **Users** | User list + roles |
| **InspectionData** | All inspection results |
| **TeamSessions** | Team inspection data |
| **Notifications** | Push notifications |
| **SharedReports** | Shared reports |
| **CustomChecklistItems** | Custom checklist items |

---

## 7. Feature-by-Feature Usage Guide

### 🔍 House Inspection

1. Tap the 🔍 "Inspect" tab
2. Fill in property information:
   - **Owner Name** (required)
   - **Address** (required)
   - House type (optional)
   - Inspector name (optional)
3. Take a photo of the house front (tap 📸 button)
4. Checklist items appear automatically when property info is filled
5. Select status for each item:
   - 🟢 **Pass** — No issues
   - 🔴 **Issue Found** — Needs fixing (add details + photo)
   - ⬜ **N/A** — Not applicable
6. Click **"Save Report"** at the bottom

### 👥 Team Inspection Mode

**Create a team (Team Leader):**
1. Toggle ☑️ "Team Inspection Mode"
2. Select members from registered users (tap their name)
3. Click **"Start Team Sync"**
4. You'll get a team code like `team_abc12345`
5. Share this code with your team members

**Join a team (Member):**
1. Login with your own account
2. Toggle ☑️ "Team Inspection Mode"
3. Click **"Join Sync"** → Enter the team code
4. Data syncs automatically every 5 seconds

**Color System:**
| Member | Color |
|--------|-------|
| Member 1 | 🔵 Blue |
| Member 2 | 🟢 Green |
| Member 3 | 🟣 Purple |
| Member 4 | 🟠 Orange |
| Member 5 | 🩷 Pink |

> Status buttons change to the color of the member who selected them (no duplicates)

### 🔁 Re-inspection (Round 2)

1. Open a previous inspection with issues (from History)
2. Click **"Re-inspect"** button
3. Take photos of each fix
4. Select **"Pass"** or **"Fail"** for each item
5. Click **"Save Report"**

**Export Comparison PDF:**
- PDF shows a comparison table: "Round 1" vs "Round 2"
- Displays photos + fix status for each item

### 📊 Reports and PDF

**View Report:**
1. Tap the 📋 "Reports" tab
2. Select the inspection you want to view
3. Click **"View Report"**

**Export PDF:**
- Cover page: White background + large house photo + property info
- Content: 6 photos per page with repair details

**Export Excel:**
- Click **"📥 Export Excel"**
- Gets a file with 3 sheets:
  1. Inspection Summary
  2. Detailed items
  3. Round 1 vs Round 2 comparison

### 🔔 Notifications

| Type | Icon | Example |
|------|------|---------|
| New team member | 👥 | "Somchai joined the inspection team at..." |
| New report | 📋 | "Inspection report for Somchai's house" |
| Shared report | 🔗 | "Somchai shared a report with you" |

- Auto-checks every 10 seconds
- Browser Push Notification for desktop/mobile
- Bell icon shows unread count

### 👥 User Management (Admin Only)

1. Go to 👥 "Users" tab
2. View all users (Active + Inactive)
3. Change role: Tap ✏️ → Inspector → Viewer → Admin
4. Enable/Disable account: Tap ⭕/🔴
5. Delete user: Tap 🗑️ → Confirm

> ⚠️ Only Admin can see "Users" and "Settings" tabs

### 🔍 Search History

1. Tap the 📜 "History" tab
2. Use the search box:
   - Search by owner name
   - Search by date
3. Clear search to see all records

---

## 8. Troubleshooting

### ❌ "Cannot connect to API"
- Check that you entered the correct API URL (must end with `/api`)
- Verify Vercel deployment was successful
- Test by opening the `/api` URL directly

### ❌ "Google Sheets connection failed"
- Check Environment Variables in Vercel:
  - `GOOGLE_SHEETS_ID` is correct
  - `SERVICE_ACCOUNT_JSON` is complete (from `{` to `}`)
- Verify Google Sheets API + Drive API are enabled
- Verify Spreadsheet is shared with the Service Account email
- Redeploy Vercel after setting Environment Variables

### ❌ Register/Login fails (error 500)
- Check Google Sheets connection (use the test button in Settings)
- Verify Service Account has Editor permission on the Spreadsheet

### ❌ Data lost after cold start
- Cause: `JWT_SECRET` is not persistent
- Fix: Set `JWT_SECRET` as a fixed value in Vercel Environment Variables

### ❌ Can't see users in management page after registering
- Verify Google Sheets connection is successful
- Hard refresh (Ctrl+Shift+R) and try again

### ❌ Can't click Save Report button
- Make sure property info is filled (owner name + address)
- Hard refresh (Ctrl+Shift+R)
- Check Console log in Browser DevTools

### ❌ PDF shows no text/tables
- Check internet connection (html2pdf.js loads from CDN)
- Hard refresh and try again

### ❌ Push notifications not working
- Check browser notification permissions
- Click 🔔 "Enable Push" in the notification panel
- Make sure notifications aren't blocked for this site

---

## 9. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_SHEETS_ID` | ✅ | - | Google Spreadsheet ID |
| `SERVICE_ACCOUNT_JSON` | ✅ | - | Service Account credentials JSON |
| `JWT_SECRET` | ❌ | auto | Secret key for token encryption |

### How to Set in Vercel
1. Vercel Dashboard → Select Project
2. Settings → Environment Variables
3. Add each variable → Click Save
4. Deployments → Select latest deployment → ⋯ → Redeploy

---

## 📞 Support

If you have installation issues:
- GitHub Issues: https://github.com/biggujp/uchi-kakunin/issues

---

*This guide is for Uchi Kakunin Setsubi v3.0 — August 29, 2026*
