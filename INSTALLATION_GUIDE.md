# 🏠 คู่มือติดตั้งและใช้งาน Uchi Kakunin Setsubi
# ระบบตรวจเช็คบ้าน (Complete Guide)

---

## 📋 สารบัญ

1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [สิ่งที่ต้องเตรียม](#2-สิ่งที่ต้องเตรียม)
3. [ตั้งค่า Google Sheets + Service Account](#3-ตั้งค่า-google-sheets--service-account)
4. [Deploy Backend บน Vercel](#4-deploy-backend-บน-vercel)
5. [Deploy Frontend บน GitHub Pages](#5-deploy-frontend-บน-github-pages)
6. [ตั้งค่าแอปและทดสอบ](#6-ตั้งค่าแอปและทดสอบ)
7. [วิธีใช้งานทีละฟีเจอร์](#7-วิธีใช้งานทีละฟีเจอร์)
8. [แก้ไขปัญหา (Troubleshooting)](#8-แก้ไขปัญหา)
9. [สรุป Environment Variables](#9-สรุป-environment-variables)

---

## 1. ภาพรวมระบบ

```
┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Frontend (HTML)   │────▶│   Backend (Flask)   │────▶│  Google Sheets   │
│   GitHub Pages      │     │   Vercel            │     │  (Database)      │
│                     │     │                     │     │                  │
│  - index.html       │     │  - Auth API         │     │  - Users         │
│  - Tailwind CSS     │     │  - Inspection API   │     │  - Inspections   │
│  - JavaScript       │     │  - Team Sessions    │     │  - TeamSessions  │
│  - Push Notifications│    │  - Notifications    │     │  - Notifications │
│                     │     │  - Google Sheets    │     │  - CustomItems   │
│                     │     │    integration      │     │  - SharedReports │
└─────────────────────┘     └─────────────────────┘     └──────────────────┘
```

| ส่วน | เทคโนโลยี | หน้าที่ |
|------|-----------|---------|
| Frontend | HTML + Tailwind CSS + JavaScript | หน้าจอใช้งาน (Mobile-First) |
| Backend | Python Flask | API + Authentication + Google Sheets |
| Database | Google Sheets | เก็บข้อมูลทั้งหมด |
| Hosting FE | GitHub Pages (ฟรี) | host ไฟล์ HTML |
| Hosting BE | Vercel (ฟรี) | host API |

---

## 2. สิ่งที่ต้องเตรียม

### 2.1 บัญชีที่ต้องมี
- [ ] **GitHub Account** — สำหรับเก็บ code + GitHub Pages
  - สมัครฟรี: https://github.com
- [ ] **Google Account** — สำหรับ Google Sheets + Google Cloud
- [ ] **Vercel Account** — สำหรับ deploy API
  - สมัครฟรี: https://vercel.com (ใช้ GitHub login ได้เลย)

### 2.2 โครงสร้างไฟล์
```
uchi-kakunin/
├── index.html              ← Frontend (ส่งขึ้น GitHub Pages)
├── public/
│   └── index.html          ← Copy อัตโนมัติสำหรับ Vercel
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

> 💡 ระบบจะสร้าง Sheet tabs (Users, InspectionData, TeamSessions, Notifications, SharedReports, CustomChecklistItems) อัตโนมัติเมื่อเริ่มใช้งาน

### ขั้นตอนที่ 3.2: สร้าง Google Cloud Project

1. เปิด https://console.cloud.google.com
2. เลือกหรือสร้าง Project ใหม่:
   - กด "Select a project" ที่มุมบนซ้าย
   - กด "NEW PROJECT"
   - ตั้งชื่อ: **Uchi Kakunin Setsubi**
   - กด "CREATE"

### ขั้นตอนที่ 3.3: เปิดใช้ API

1. ใน Google Cloud Console → เมนูซ้าย → **APIs & Services** → **Library**
2. ค้นหา **"Google Sheets API"** → กด **"ENABLE"**
3. ค้นหา **"Google Drive API"** → กด **"ENABLE"**

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

1. เปิด Google Spreadsheet ที่สร้างไว้
2. กด **"Share"** ที่มุมบนขวา
3. วาง **Email ของ Service Account** (หาได้ในไฟล์ JSON บรรทัด `client_email`)
   - ตัวอย่าง: `uchi-kakunin-api@your-project.iam.gserviceaccount.com`
4. เลือก Permission: **"Editor"**
5. กด **"Send"**

### ขั้นตอนที่ 3.7: เตรียม Service Account JSON

1. เปิดไฟล์ JSON ที่ดาวน์โหลดด้วย Text Editor (VS Code, Notepad++)
2. คัดลอก **เนื้อหาทั้งหมด** ในไฟล์ (ตั้งแต่ `{` ถึง `}`)
3. บันทึกไว้ จะใช้ตอนตั้งค่า Vercel Environment Variable

> ⚠️ **สำคัญ:** ห้ามแชร์ไฟล์นี้สาธารณะเด็ดขาด!

---

## 4. Deploy Backend บน Vercel

### ขั้นตอนที่ 4.1: Login เข้า Vercel

1. เปิด https://vercel.com
2. กด **"Log In"**
3. เลือก **"Continue with GitHub"**

### ขั้นตอนที่ 4.2: Import Project

1. ใน Vercel Dashboard → กด **"Add New..."** → **"Project"**
2. เลือกแท็บ **"Import Git Repository"**
3. ค้นหา repo `uchi-kakunin` → กด **"Import"**

### ขั้นตอนที่ 4.3: ตั้งค่า Environment Variables

> ⚠️ **สำคัญมาก!** ต้องตั้งค่าก่อนกด Deploy

ในหน้า Project → กดแท็บ **"Environment Variables"** → เพิ่ม 2-3 ตัวนี้:

**Variable 1: GOOGLE_SHEETS_ID** ✅ จำเป็น
| Field | Value |
|-------|-------|
| Name | `GOOGLE_SHEETS_ID` |
| Value | `1AbCdEfGhIjKlMnOpQrStUvWxYz` (Spreadsheet ID ที่คัดลอกไว้) |

**Variable 2: SERVICE_ACCOUNT_JSON** ✅ จำเป็น
| Field | Value |
|-------|-------|
| Name | `SERVICE_ACCOUNT_JSON` |
| Value | (วางเนื้อหาไฟล์ JSON ทั้งหมด) |

> 💡 คัดลอกทั้งหมดจาก `{` ถึง `}` ในไฟล์ JSON

**Variable 3: JWT_SECRET** ❌ ไม่บังคับ
| Field | Value |
|-------|-------|
| Name | `JWT_SECRET` |
| Value | (สุ่ม string ยาว ≥32 ตัวอักษร) |

> 💡 วิธีสุ่ม: เปิด terminal แล้วพิมพ์:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> ถ้าไม่ตั้งค่า ระบบจะ derive จาก Google Sheets ID อัตโนมัติ

### ขั้นตอนที่ 4.4: Deploy

1. ตั้งค่าเสร็จ → กด **"Deploy"**
2. รอ 1-2 นาที ให้ build เสร็จ
3. กด **"Continue to Dashboard"**
4. จะได้ URL ประมาณ:
   ```
   https://uchi-kakunin.vercel.app
   ```
5. กดเปิดลิงก์ทดสอบ API:
   ```
   https://uchi-kakunin.vercel.app/api
   ```
   ถ้าเห็น `{"status":"ok","message":"House Inspection API",...}` = สำเร็จ!

### ขั้นตอนที่ 4.5: Redeploy หลังแก้โค้ด

ทุกครั้งที่ push โค้ดขึ้น GitHub main branch → Vercel จะ auto-deploy ให้อัตโนมัติ

ถ้าต้องการ redeploy ด้วยตัวเอง:
1. Vercel Dashboard → เลือก Project
2. ไปแท็บ **"Deployments"**
3. กดปุ่ม **⋯** → **"Redeploy"**

---

## 5. Deploy Frontend บน GitHub Pages

### ขั้นตอนที่ 5.1: Push ไฟล์ขึ้น GitHub

```bash
# ในโฟลเดอร์โปรเจกต์
git init
git add .
git commit -m "Initial commit - Uchi Kakunin Setsubi"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/uchi-kakunin.git
git push -u origin main
```

### ขั้นตอนที่ 5.2: เปิด GitHub Pages

1. ไปที่ Repository บน GitHub
2. กดแท็บ **"Settings"**
3. เมนูซ้าย → เลือก **"Pages"**
4. ส่วน Source:
   - Branch: **main**
   - Folder: **/ (root)**
5. กด **"Save"**
6. รอ 1-2 นาที → จะได้ URL ประมาณ:
   ```
   https://YOUR_USERNAME.github.io/uchi-kakunin/
   ```

---

## 6. ตั้งค่าแอปและทดสอบ

### ขั้นตอนที่ 6.1: ตั้งค่า API URL

1. เปิดแอป GitHub Pages URL
2. กดไอคอน 👤 มุมบนขวา → กด **"ตั้งค่า"**
3. ช่อง **API Base URL (Vercel):** ใส่ URL ของ Vercel + `/api`
   ```
   https://uchi-kakunin.vercel.app/api
   ```
4. กด **"บันทึกการตั้งค่า"**

### ขั้นตอนที่ 6.2: ทดสอบการเชื่อมต่อ

1. ในหน้าตั้งค่า → กดปุ่ม **"🔍 ทดสอบการเชื่อมต่อ Google Sheets"**
2. ผลลัพธ์:
   - ✅ **เชื่อมต่อ Google Sheets สำเร็จ!** → พร้อมใช้งาน
   - ❌ **เชื่อมต่อไม่สำเร็จ** → ตรวจสอบ Environment Variables

### ขั้นตอนที่ 6.3: สมัครสมาชิก Admin คนแรก

1. กดไอคอน 👤 → **"เข้าสู่ระบบ / สมัครสมาชิก"**
2. กดลิงก์ **"สมัครสมาชิก"**
3. กรอกข้อมูล:
   - **Username:** `admin`
   - **ชื่อที่ต้องการแสดง:** `ผู้ดูแลระบบ`
   - **Password:** (ตั้งรหัสผ่าน)
4. กด **"สมัครสมาชิก"**

> 💡 **เปลี่ยนเป็น Admin:** เปิด Google Sheets → แท็บ "Users" → เปลี่ยน Role จาก `inspector` เป็น `admin`

### ขั้นตอนที่ 6.4: ทดสอบใช้งาน

**ทดสอบ inspection แรก:**
1. กดแท็บ 🔍 "ตรวจเช็ค"
2. กรอกข้อมูลทรัพย์สิน (ชื่อเจ้าของ + ที่อยู่)
3. ถ่ายรูปหน้าบ้าน
4. เลือกหมวด → แตะ "ผ่าน" หรือ "มีปัญหา"
5. กด **"บันทึกรายการ"** ด้านล่างสุด
6. ดูรายงาน + Export PDF

**ทดสอบ Multi-User:**
1. ออกจากระบบ
2. สมัครสมาชิกใหม่
3. Login ด้วยบัญชีใหม่
4. ลอง inspection ใหม่

**ทดสอบ Team Mode:**
1. Login ด้วยบัญชี Admin
2. เปิด ☑️ "โหมดทีมตรวจ"
3. เลือกสมาชิกทีม
4. กด "เริ่มซิงค์ทีม"
5. -members ใช้รหัสทีมเข้าร่วม

### ขั้นตอนที่ 6.5: ตรวจสอบ Google Sheets

เปิด Google Spreadsheet จะเห็นแท็บ:
| แท็บ | ข้อมูล |
|------|--------|
| **Users** | รายชื่อผู้ใช้ + บทบาท |
| **InspectionData** | ผลตรวจทั้งหมด |
| **TeamSessions** | ข้อมูลทีมตรวจ |
| **Notifications** | การแจ้งเตือน |
| **SharedReports** | รายงานที่แชร์ |
| **CustomChecklistItems** | รายการที่เพิ่มเอง |

---

## 7. วิธีใช้งานทีละฟีเจอร์

### 🔍 ตรวจเช็คบ้าน ( Inspection)

1. กดแท็บ 🔍 "ตรวจเช็ค"
2. กรอกข้อมูลทรัพย์สิน:
   - **ชื่อเจ้าของบ้าน** (จำเป็น)
   - **ที่อยู่** (จำเป็น)
   - ประเภทบ้าน (optional)
   - ชื่อผู้ตรวจ (optional)
3. ถ่ายรูปหน้าบ้าน (กดปุ่ม 📸)
4. รายการตรวจเช็คจะแสดงอัตโนมัติเมื่อกรอกข้อมูลครบ
5. เลือกสถานะแต่ละรายการ:
   - 🟢 **ผ่าน** — ไม่มีปัญหา
   - 🔴 **มีปัญหา** — ต้องแก้ไข (กรอกรายละเอียด + ถ่ายรูป)
   - ⬜ **N/A** — ไม่มีรายการให้ตรวจ
6. กด **"บันทึกรายการ"** ด้านล่างสุด

### 👥 โหมดทีมตรวจ (Team Inspection)

**สร้างทีม (หัวหน้าทีม):**
1. เปิด ☑️ "โหมดทีมตรวจ"
2. เลือกสมาชิกจาก user ที่ลงทะเบียนแล้ว (แตะชื่อ)
3. กด **"เริ่มซิงค์ทีม"**
4. จะได้รหัสทีม เช่น `team_abc12345`
5. บอกทีมให้ใช้รหัสนี้เข้าร่วม

**เข้าร่วมทีม (สมาชิก):**
1. Login ด้วยบัญชีของตัวเอง
2. เปิด ☑️ "โหมดทีมตรวจ"
3. กด **"เข้าร่วมซิงค์"** → ใส่รหัสทีม
4. ข้อมูลจะซิงค์อัตโนมัติทุก 5 วินาที

**ระบบสี:**
| สมาชิก | สี |
|---------|-----|
| คนที่ 1 | 🔵 น้ำเงิน |
| คนที่ 2 | 🟢 เขียว |
| คนที่ 3 | 🟣 ม่วง |
| คนที่ 4 | 🟠 ส้ม |
| คนที่ 5 | 🩷 ชมพู |

> สถานะปุ่มจะเปลี่ยนเป็นสีของสมาชิกที่เลือก (ไม่ซ้ำกัน)

### 🔁 ตรวจรอบ 2 (Re-inspection)

1. เปิด inspection เดิมที่มีปัญหา (จากประวัติ)
2. กดปุ่ม **"ตรวจรอบ 2"**
3. ถ่ายรูปการแก้ไขแต่ละจุด
4. เลือก **"ผ่าน"** หรือ **"ไม่ผ่าน"** สำหรับแต่ละจุด
5. กด **"บันทึกรายการ"**

**Export PDF เปรียบเทียบ:**
- PDF จะแสดง ตารางเปรียบเทียบ "ผลตรวจครั้งที่ 1" vs "ผลตรวจครั้งที่ 2"
- แสดงรูปถ่าย + สถานะแก้ไขของแต่ละจุด

### 📊 รายงานและ PDF

**ดูรายงาน:**
1. กดแท็บ 📋 "รายงาน"
2. เลือกรายการ inspection ที่ต้องการดู
3. กด **"ดูรายงาน"**

**Export PDF:**
- หน้าปก: สีขาว + รูปบ้านใหญ่ + ข้อมูลทรัพย์สิน
- เนื้อหา: ตาราง 6 รูปต่อหน้า พร้อมรายละเอียดจุดแก้ไข

**Export Excel:**
- กดปุ่ม **"📥 Export Excel"**
- ได้ไฟล์ 3 ชีท:
  1. สรุปผลตรวจ
  2. รายละเอียดแต่ละรายการ
  3. เปรียบเทียบ รอบ 1 vs รอบ 2

### 🔔 การแจ้งเตือน (Notifications)

| ประเภท | ไอคอน | ตัวอย่าง |
|--------|--------|----------|
| สมาชิกใหม่เข้าทีม | 👥 | "สมชาย เข้าร่วมทีมตรวจที่..." |
| รายงานใหม่ | 📋 | "สรุปผลตรวจบ้าน สมศักดิ์" |
| แชร์รายงาน | 🔗 | "สมชาย แชร์รายงานมาให้คุณ" |

- ตรวจสอบอัตโนมัติทุก 10 วินาที
- Push Notification (Browser) สำหรับ desktop/mobile
- ไอ귓 Bell แสดง unread count

### 👥 จัดการผู้ใช้ (Admin Only)

1. ไปแท็บ 👥 "ผู้ใช้"
2. ดูรายชื่อ user ทั้งหมด (Active + Inactive)
3. เปลี่ยนบทบาท: กดปุ่ม ✏️ → Inspector → Viewer → Admin
4. เปิด/ปิดบัญชี: กดปุ่ม ⭕/🔴
5. ลบผู้ใช้: กดปุ่ม 🗑️ → ยืนยัน

> ⚠️ เฉพาะ Admin เท่านั้นที่เห็นแท็บ "ผู้ใช้" และ "ตั้งค่า"

### 🔍 ค้นหาประวัติ

1. กดแท็บ 📜 "ประวัติ"
2. ใช้ช่องค้นหา:
   - ค้นตามชื่อเจ้าของ
   - ค้นตามวันที่
3. กดล้างค้นหาเพื่อดูทั้งหมด

---

## 8. แก้ไขปัญหา

### ❌ "เชื่อมต่อ API ไม่ได้"
- ตรวจสอบว่าใส่ API URL ถูกต้อง (ต้องลงท้าย `/api`)
- ตรวจสอบว่า Vercel Deploy สำเร็จแล้ว
- เปิด URL `/api` ตรงๆ ทดสอบ

### ❌ "เชื่อมต่อ Google Sheets ไม่สำเร็จ"
- ตรวจสอบ Environment Variables ใน Vercel:
  - `GOOGLE_SHEETS_ID` ถูกต้อง
  - `SERVICE_ACCOUNT_JSON` วางครบถ้วน (ตั้งแต่ `{` ถึง `}`)
- ตรวจสอบว่าเปิด Google Sheets API + Drive API แล้ว
- ตรวจสอบว่า Share Spreadsheet ให้ Service Account email แล้ว
- Redeploy Vercel หลังตั้งค่า Environment Variables

### ❌ Register/Login ไม่ได้ (error 500)
- ตรวจสอบ Google Sheets connection (ใช้ปุ่มทดสอบใน Settings)
- ตรวจสอบว่า Service Account มีสิทธิ์ Editor ใน Spreadsheet

### ❌ ข้อมูลหายหลัง Cold Start
- สาเหตุ: `JWT_SECRET` ไม่คงที่
- แก้: ตั้งค่า `JWT_SECRET` เป็นค่าคงที่ใน Vercel Environment Variables

### ❌ สมัครสมาชิกแล้วไม่เห็น user ในหน้าจัดการ
- ตรวจสอบว่า Google Sheets เชื่อมต่อสำเร็จ
- Hard refresh (Ctrl+Shift+R) แล้วลองใหม่

### ❌ กดปุ่มบันทึกรายการไม่ได้
- ตรวจสอบว่ากรอกข้อมูลทรัพย์สินครบ (ชื่อเจ้าของ + ที่อยู่)
- Hard refresh (Ctrl+Shift+R)
- ตรวจสอบ Console log ใน Browser DevTools

### ❌ PDF ไม่แสดงข้อความ/ตาราง
- ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต (html2pdf.js โหลดจาก CDN)
- Hard refresh แล้วลองใหม่

### ❌ Push Notification ไม่ทำงาน
- ตรวจสอบว่าเบราว์เซอร์ให้สิทธิ์ Notification
- กดปุ่ม 🔔 "เปิด Push" ใน notification panel
- ตรวจสอบว่าไม่ได้บล็อก notification สำหรับเว็บนี้

---

## 9. สรุป Environment Variables

| Variable | Required | ค่าเริ่มต้น | คำอธิบาย |
|----------|----------|------------|---------|
| `GOOGLE_SHEETS_ID` | ✅ | - | Google Spreadsheet ID |
| `SERVICE_ACCOUNT_JSON` | ✅ | - | JSON ของ Service Account credentials |
| `JWT_SECRET` | ❌ | auto | Secret key สำหรับเข้ารหัส token |

### วิธีตั้งค่าใน Vercel
1. Vercel Dashboard → เลือก Project
2. Settings → Environment Variables
3. เพิ่มแต่ละตัว → กด Save
4. Deployments → เลือก deployment ล่าสุด → ⋯ → Redeploy

---

## 📞 ติดต่อ

ถ้ามีปัญหาในการติดตั้ง:
- GitHub Issues: https://github.com/biggujp/uchi-kakunin/issues

---

*คู่มือนี้สำหรับ Uchi Kakunin Setsubi v3.0 — วันที่ 29 สิงหาคม 2569*
