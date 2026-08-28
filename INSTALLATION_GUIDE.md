# 🏠 คู่มือติดตั้ง Uchi Kakunin Setsubi
# ระบบตรวจเช็คบ้าน (Complete Installation Guide)

---

## 📋 สารบัญ
1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [สิ่งที่ต้องเตรียม](#2-สิ่งที่ต้องเตรียม)
3. [ตั้งค่า Google Sheets + Service Account](#3-ตั้งค่า-google-sheets--service-account)
4. [Deploy Frontend บน GitHub Pages](#4-deploy-frontend-บน-github-pages)
5. [Deploy Backend บน Vercel](#5-deploy-backend-บน-vercel)
6. [ตั้งค่าแอปและทดสอบ](#6-ตั้งค่าแอปและทดสอบ)
7. [แก้ไขปัญหา (Troubleshooting)](#7-แก้ไขปัญหา)
8. [วิธีใช้งานเบื้องต้น](#8-วิธีใช้งานเบื้องต้น)

---

## 1. ภาพรวมระบบ

```
┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Frontend (HTML)   │────▶│   Backend (Flask)   │────▶│  Google Sheets   │
│   GitHub Pages      │     │   Vercel            │     │  (Database)      │
│                     │     │                     │     │                  │
│  - index.html       │     │  - API endpoints    │     │  - Users         │
│  - Tailwind CSS     │     │  - Authentication   │     │  - Inspections   │
│  - JavaScript       │     │  - Google Sheets    │     │  - Custom Items  │
│  - Offline Support  │     │    integration      │     │  - Notifications │
└─────────────────────┘     └─────────────────────┘     │  - Sync Queue    │
                                                        └──────────────────┘
```

**ส่วนประกอบ:**
| ส่วน | เทคโนโลยี | หน้าที่ |
|------|-----------|---------|
| Frontend | HTML + Tailwind CSS + JavaScript | หน้าจอใช้งาน |
| Backend | Python Flask | API + Logic |
| Database | Google Sheets | เก็บข้อมูล |
| Hosting FE | GitHub Pages (ฟรี) | host ไฟล์ HTML |
| Hosting BE | Vercel (ฟรี) | host API |

---

## 2. สิ่งที่ต้องเตรียม

### 2.1 บัญชีที่ต้องมี
- [ ] **GitHub Account** - สำหรับเก็บ code + GitHub Pages
  - สมัครฟรี: https://github.com
- [ ] **Google Account** - สำหรับ Google Sheets + Google Cloud
- [ ] **Vercel Account** - สำหรับ deploy API
  - สมัครฟรี: https://vercel.com (ใช้ GitHub login ได้เลย)

### 2.2 ดาวน์โหลดไฟล์
ดาวน์โหลดไฟล์โปรเจกต์จาก GitHub:
```bash
git clone https://github.com/YOUR_USERNAME/uchi-kakunin-setsubi.git
cd uchi-kakunin-setsubi
```

หรือดาวน์โหลด ZIP:
1. เปิด repo บน GitHub
2. กด Code → Download ZIP
3. แตกไฟล์

### 2.3 โครงสร้างไฟล์
```
uchi-kakunin-setsubi/
├── index.html              ← Frontend (ส่งขึ้น GitHub Pages)
├── api/
│   └── index.py            ← Backend API (ส่งขึ้น Vercel)
├── vercel.json             ← Config สำหรับ Vercel
├── requirements.txt        ← Python dependencies
├── README.md
└── INSTALLATION_GUIDE.md   ← คู่มือนี้
```

---

## 3. ตั้งค่า Google Sheets + Service Account

### ขั้นตอนที่ 3.1: สร้าง Google Spreadsheet

1. เปิด https://sheets.google.com
2. กด **"+ สเปรดชีตใหม่"**
3. ตั้งชื่อว่า **"Uchi Kakunin Setsubi Database"**
4. คัดลอก **Spreadsheet ID** จาก URL:
   ```
   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID_HERE]/edit
   ```
   ตัวอย่าง: ถ้า URL คือ `https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit`
   → Spreadsheet ID คือ `1AbCdEfGhIjKlMnOpQrStUvWxYz`

5. **บันทึก Spreadsheet ID ไว้** จะใช้ตอนตั้งค่า Vercel

### ขั้นตอนที่ 3.2: สร้าง Google Cloud Project

1. เปิด https://console.cloud.google.com
2. เลือกหรือสร้าง Project ใหม่:
   - กด "Select a project" ที่มุมบนซ้าย
   - กด "NEW PROJECT"
   - ตั้งชื่อ: **Uchi Kakunin Setsubi**
   - กด "CREATE"

### ขั้นตอนที่ 3.3: เปิดใช้ Google Sheets API

1. ใน Google Cloud Console → เมนูซ้าย → **APIs & Services** → **Library**
2. ค้นหา **"Google Sheets API"**
3. กดเข้าไป → กด **"ENABLE"**
4. ค้นหา **"Google Drive API"** (ต้องเปิดด้วย)
5. กดเข้าไป → กด **"ENABLE"**

### ขั้นตอนที่ 3.4: สร้าง Service Account

1. เมนูซ้าย → **APIs & Services** → **Credentials**
2. กด **"+ CREATE CREDENTIALS"** → เลือก **"Service Account"**
3. ตั้งค่า:
   - **Service account name:** `uchi-kakunin-api`
   - **Description:** `API for Uchi Kakunin Setsubi`
   - กด "CREATE AND CONTINUE"
4. (Optional) เลือก Role → กด "CONTINUE"
5. กด **"DONE"**

### ขั้นตอนที่ 3.5: สร้าง Key (JSON)

1. คลิกที่ Service Account ที่สร้างไว้
2. ไปที่แท็บ **"KEYS"**
3. กด **"ADD KEY"** → **"Create new key"**
4. เลือก **JSON** → กด **"CREATE"**
5. ไฟล์ JSON จะดาวน์โหลดอัตโนมัติ → **เก็บไฟล์นี้ไว้ให้ดี!**

### ขั้นตอนที่ 3.6: เปิดสิทธิ์เข้าถึง Spreadsheet

**วิธี A: แชร์ Spreadsheet (ง่ายที่สุด)**
1. เปิด Google Spreadsheet ที่สร้างไว้
2. กด **"Share"** ที่มุมบนขวา
3. วาง **Email ของ Service Account** (หาได้ในไฟล์ JSON ที่ดาวน์โหลด บรรทัด `client_email`)
   - ตัวอย่าง: `uchi-kakunin-api@your-project.iam.gserviceaccount.com`
4. เลือก Permission: **"Editor"**
5. กด **"Send"**

**วิธี B: ใช้ Service Account Email ตรง**
1. เปิด Spreadsheet → Share
2. เพิ่ม Service Account email → Editor

### ขั้นตอนที่ 3.7: เตรียม Service Account JSON

1. เปิดไฟล์ JSON ที่ดาวน์โหลดด้วย Text Editor (Notepad++, VS Code)
2. คัดลอก **ข้อความทั้งหมด** ในไฟล์
3. บันทึกไว้ จะใช้ตอนตั้งค่า Vercel Environment Variable

**ตัวอย่างเนื้อหาไฟล์ JSON:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "uchi-kakunin-api@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  ...
}
```

> ⚠️ **สำคัญ:** ห้ามแชร์ไฟล์นี้สาธารณะเด็ดขาด!

---

## 4. Deploy Frontend บน GitHub Pages

### ขั้นตอนที่ 4.1: สร้าง Repository ใหม่บน GitHub

1. เปิด https://github.com/new
2. ตั้งค่า:
   - **Repository name:** `uchi-kakunin-setsubi`
   - **Public** (ต้องเป็น Public ถ้าใช้ GitHub Pages ฟรี)
   - กด **"Create repository"**

### ขั้นตอนที่ 4.2: Push ไฟล์ขึ้น GitHub

```bash
# ในโฟลเดอร์โปรเจกต์
git init
git add index.html
git commit -m "Initial commit - Uchi Kakunin Setsubi Frontend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/uchi-kakunin-setsubi.git
git push -u origin main
```

### ขั้นตอนที่ 4.3: เปิด GitHub Pages

1. ไปที่ Repository บน GitHub
2. กดแท็บ **"Settings"**
3. เมนูซ้าย → เลือก **"Pages"**
4. ส่วน Source:
   - Branch: **main**
   - Folder: **/ (root)**
5. กด **"Save"**
6. รอ 1-2 นาที → จะได้ URL ประมาณ:
   ```
   https://YOUR_USERNAME.github.io/uchi-kakunin-setsubi/
   ```
7. กดเปิดลิงก์ทดสอบ

---

## 5. Deploy Backend บน Vercel

### ขั้นตอนที่ 5.1: Login เข้า Vercel

1. เปิด https://vercel.com
2. กด **"Log In"**
3. เลือก **"Continue with GitHub"** (ใช้บัญชี GitHub เดียวกัน)

### ขั้นตอนที่ 5.2: Import Project

1. ใน Vercel Dashboard → กด **"Add New..."** → **"Project"**
2. เลือกแท็บ **"Import Git Repository"**
3. ค้นหา repo `uchi-kakunin-setsubi` → กด **"Import"**

### ขั้นตอนที่ 5.3: ตั้งค่า Environment Variables

> ⚠️ **สำคัญมาก!** ต้องตั้งค่าก่อนกด Deploy

ในหน้าตั้งค่า Project → กดแท็บ **"Environment Variables"** → เพิ่ม 2 ตัวนี้:

**Variable 1: GOOGLE_SHEETS_ID**
| Field | Value |
|-------|-------|
| Name | `GOOGLE_SHEETS_ID` |
| Value | `1AbCdEfGhIjKlMnOpQrStUvWxYz` (Spreadsheet ID ที่คัดลอกไว้) |

กด **"Add"**

**Variable 2: SERVICE_ACCOUNT_JSON**
| Field | Value |
|-------|-------|
| Name | `SERVICE_ACCOUNT_JSON` |
| Value | (วางเนื้อหาไฟล์ JSON ทั้งหมด) |

> 💡 **技巧:** คัดลอกทั้งหมดจาก `{` ถึง `}` ในไฟล์ JSON

กด **"Add"**

**Variable 3: JWT_SECRET (Recommended)**
| Field | Value |
|-------|-------|
| Name | `JWT_SECRET` |
| Value | (สุ่ม string ยาวอย่างน้อย 32 ตัวอักษร) |

> 💡 **JWT_SECRET** ใช้สำหรับเข้ารหัส token ให้ปลอดภัย ถ้าไม่ตั้งค่า ระบบจะสร้างจาก Google Sheets ID อัตโนมัติ แต่แนะนำให้ตั้งเองจะมั่นคงกว่า
>
> **วิธีสุ่ม:** เปิด terminal แล้วพิมพ์:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

กด **"Add"**

### ขั้นตอนที่ 5.4: Deploy

1. ตั้งค่าเสร็จ → กด **"Deploy"**
2. รอ 1-2 นาที ให้ build เสร็จ
3. กด **"Continue to Dashboard"**
4. จะได้ URL ประมาณ:
   ```
   https://uchi-kakunin-setsubi-xxxx.vercel.app
   ```
5. กดเปิดลิงก์ทดสอบ API:
   ```
   https://uchi-kakunin-setsubi-xxxx.vercel.app/api
   ```
   ถ้าเห็น `{"status":"ok","message":"House Inspection API",...}` = สำเร็จ!

### ขั้นตอนที่ 5.5: ตั้ง Custom Domain (Optional)

1. ใน Vercel Dashboard → Settings → Domains
2. เพิ่ม domain ที่ต้องการ
3. ตั้งค่า DNS ตามที่ Vercel แนะนำ

---

## 6. ตั้งค่าแอปและทดสอบ

### ขั้นตอนที่ 6.1: เปิดแอป

เปิด URL ของ GitHub Pages ที่ได้จากขั้นตอนที่ 4.3

### ขั้นตอนที่ 6.2: ตั้งค่า API URL

1. กดแท็บ **"ตั้งค่า"** (⚙️)
2. ช่อง **API Base URL (Vercel):** ใส่ URL ของ Vercel + `/api`
   ```
   https://uchi-kakunin-setsubi-xxxx.vercel.app/api
   ```
3. กด **"บันทึกการตั้งค่า"**

> 💡 **Offline Mode:** ถ้ายังไม่ได้ตั้งค่า Google Sheets หรือ API URL แอปจะทำงานแบบ **Offline Mode** — ข้อมูลจะบันทึกลง localStorage ในเครื่อง สมัครสมาชิก/เข้าสู่ระบบได้ทันทีโดยไม่ต้องรอ backend

### ขั้นตอนที่ 6.3: สมัครสมาชิก (สร้าง Admin)

1. กดไอคอน User (👤) มุมบนขวา
2. กด **"เข้าสู่ระบบ / สมัครสมาชิก"**
3. กดลิงก์ **"สมัครสมาชิก"**
4. กรอกข้อมูล:
   - **Username:** `admin`
   - **ชื่อที่ต้องการแสดง:** `ผู้ดูแลระบบ`
   - **Password:** (ตั้งรหัสผ่าน)
   - **Role:** เลือก **Inspector** (แล้วเปลี่ยนเป็น Admin ทีหลัง หรือแก้ใน Google Sheets โดยตรง)
5. กด **"สมัครสมาชิก"**

> 💡 **เปลี่ยนเป็น Admin:** เปิด Google Sheets → แท็บ "Users" → เปลี่ยน Role เป็น `admin`

### ขั้นตอนที่ 6.4: ทดสอบใช้งาน

**ทดสอบ inspection แรก:**
1. กดแท็บ **"ตรวจเช็ค"**
2. กรอกข้อมูลทรัพย์สิน:
   - ชื่อเจ้าของบ้าน
   - ที่อยู่
   - ประเภทบ้าน
3. ถ่ายรูปหน้าบ้าน
4. เลือกหมวด → แตะ "ผ่าน" หรือ "มีปัญหา"
5. กด **"บันทึกรายงานการตรวจ"**
6. ดูรายงาน + Export PDF

**ทดสอบ Multi-User:**
1. ออกจากระบบ
2. สมัครสมาชิกใหม่ (inspector)
3. Login ด้วยบัญชีใหม่
4. ลอง inspection ใหม่

**ทดสอบ Offline Mode:**
1. **ยังไม่ได้ตั้งค่า Google Sheets** → Login/Register ได้ทันที (Offline Mode)
2. ทำ inspection → บันทึกลง localStorage
3. ตั้งค่า Google Sheets แล้ว → กด "บังคับซิงค์" → ข้อมูลจะอัปโหลดอัตโนมัติ

**ทดสอบ Offline ตอนมีสัญญาณ:**
1. ปิด WiFi / โหมดเครื่องบิน
2. ทำ inspection → จะเห็น Toast "ไม่มีสัญญาณ"
3. เปิด WiFi กลับ → จะซิงค์อัตโนมัติ

### ขั้นตอนที่ 6.5: ตรวจสอบ Google Sheets

เปิด Google Spreadsheet จะเห็นแท็บ:
- **Users** → รายชื่อผู้ใช้
- **InspectionData** → ผลตรวจ
- **CustomChecklistItems** → รายการที่เพิ่มเอง
- **Notifications** → การแจ้งเตือน
- **SharedReports** → รายการแชร์
- **SyncQueue** → คิวซิงค์ออฟไลน์
- **ActivityLog** → ประวัติการใช้งาน

---

## 7. แก้ไขปัญหา

### ❌ "เชื่อมต่อ API ไม่ได้"
- ตรวจสอบว่าใส่ API URL ถูกต้อง (ต้องลงท้าย `/api`)
- ตรวจสอบว่า Vercel Deploy สำเร็จแล้ว
- เปิด URL `/api` ตรงๆ ทดสอบ
- **ถ้ายังไม่ได้ deploy Vercel** → แอปจะทำงาน Offline Mode ได้เลย ไม่ต้องรอ

### ❌ "Google Sheets not configured"
- ตรวจสอบ Environment Variables ใน Vercel:
  - `GOOGLE_SHEETS_ID` ถูกต้อง
  - `SERVICE_ACCOUNT_JSON` วางครบถ้วน
- ตรวจสอบว่าเปิด Google Sheets API + Drive API แล้ว
- ตรวจสอบว่า Share Spreadsheet ให้ Service Account email แล้ว
- **ถ้ายังไม่ได้ตั้งค่า** → แอปจะทำงาน Offline Mode อัตโนมัติ ไม่ error

### ❌ "Unauthorized" / Login ไม่ได้
- Token หมดอายุ (24 ชม.) → Login ใหม่
- ตรวจสอบว่า `JWT_SECRET` ตั้งค่าถูกต้อง (ต้องคงที่ ห้ามเปลี่ยนบ่อย)
- ตรวจสอบว่า AuthService ทำงานปกติ

### ❌ ข้อมูลหายหลัง Cold Start
- สาเหตุ: `JWT_SECRET` ไม่คงที่ (Vercel generate ใหม่ทุกครั้ง)
- แก้: ตั้งค่า `JWT_SECRET` เป็นค่าคงที่ใน Vercel Environment Variables
- ระบบจะ derive จาก Google Sheets ID อัตโนมัติถ้าไม่ได้ตั้ง แต่แนะนำตั้งเอง

### ❌ PDF Export ไม่ทำงาน
- ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
- html2pdf.js โหลดจาก CDN ต้องมีเน็ต

### ❌ ข้อมูลไม่ซิงค์
- กด "บังคับซิงค์ตอนนี้" ในหน้า Settings
- ตรวจสอบ Network Tab ใน Browser DevTools
- ตรวจสอบว่า `GOOGLE_SHEETS_ID` และ `SERVICE_ACCOUNT_JSON` ถูกต้อง

---

## 8. วิธีใช้งานเบื้องต้น

### 👤 สำหรับ Admin
1. Login ด้วยบัญชี Admin
2. จัดการผู้ใช้ในแท็บ "ผู้ใช้"
3. ดูผลตรวจทั้งหมด
4. รับ notification เมื่อมี inspection ใหม่

### 🔍 สำหรับ Inspector
1. Login ด้วยบัญชี Inspector
2. ทำ inspection → บันทึกรายงาน
3. Export PDF ส่งให้ลูกค้า
4. แชร์รายงานให้คนอื่นดู

### 👁️ สำหรับ Viewer
1. Login ด้วยบัญชี Viewer
2. ดูเฉพาะรายงานที่ถูกแชร์มาให้

---

## 9. Offline Mode (โหมดออฟไลน์)

### คืออะไร?
ระบบ **Offline Mode** ช่วยให้แอปทำงานได้แม้ไม่มี Google Sheets หรือ Backend — เหมาะสำหรับ:
- ทดสอบระบบก่อน deploy
- ใช้งานในพื้นที่ไม่มีอินเทอร์เน็ต
- ตั้งค่าทีละส่วน

### วิธีเปิด Offline Mode
ถ้ายังไม่ได้ตั้งค่า Google Sheets → แอปจะเข้า Offline Mode **อัตโนมัติ**:

1. เปิดแอป → ไม่ต้องตั้งค่าอะไรเพิ่ม
2. กดสมัครสมาชิก / Login → จะได้ token ทันที
3. ทำ inspection → ข้อมูลบันทึกลง localStorage
4. ข้อมูลจะเก็บในเครื่องเท่านั้น (ไม่ส่งขึ้น server)

### สิ่งที่ใช้งานได้ใน Offline Mode
| Feature | ใช้ได้? | หมายเหตุ |
|---------|--------|----------|
| Login / Register | ✅ | บันทึก token ใน localStorage |
| ทำ Inspection | ✅ | บันทึกลง localStorage |
| Export PDF | ✅ | ทำงานฝั่ง client |
| เพิ่มรายการตรวจสอบเอง | ✅ | บันทึกลง localStorage |
| Multi-User / Role | ⚠️ | ใช้ได้ใน session เดียว (ไม่ sync ข้ามเครื่อง) |
| Notification | ❌ | ต้องมี backend |
| Share รายงาน | ❌ | ต้องมี backend |
| ซิงค์ข้ามเครื่อง | ❌ | ต้องมี Google Sheets |

### วิธีซิงค์ข้อมูลจาก Offline → Online
เมื่อตั้งค่า Google Sheets เรียบร้อยแล้ว:

1. ไปแท็บ **ตั้งค่า** (⚙️)
2. ใส่ API URL ของ Vercel
3. กด **"บันทึกการตั้งค่า"**
4. Login ด้วยบัญชีเดิม
5. กด **"บังคับซิงค์ตอนนี้"**
6. ข้อมูล inspection ที่บันทึกไว้จะถูกอัปโหลดขึ้น Google Sheets อัตโนมัติ

### JWT_SECRET
`JWT_SECRET` ใช้เข้ารหัส token ให้ปลอดภัย:

| สถานะ | ผลลัพธ์ |
|--------|---------|
| ไม่ตั้งค่า | ระบบ derive จาก Google Sheets ID (ใช้ได้แต่ไม่แนะนำ生产) |
| ตั้งค่าคงที่ | ✅ แนะนำ — token ปลอดภัย ใช้ได้ยาว |
| เปลี่ยนบ่อย | ⚠️ token เก่าจะใช้ไม่ได้ ต้อง Login ใหม่ |

---

## 📞 ติดต่อ

ถ้ามีปัญหาในการติดตั้ง ติดต่อได้ที่:
- GitHub Issues: https://github.com/YOUR_USERNAME/uchi-kakunin-setsubi/issues

---

*คู่มือนี้สำหรับ Uchi Kakunin Setsubi v2.1*
