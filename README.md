# 🏠 Uchi Kakunin Setsubi | ระบบตรวจเช็คบ้าน

ระบบเว็บแอปพลิเคชันสำหรับตรวจเช็คบ้าน พร้อมรายงานจุดที่ต้องแก้ไข
รองรับ Mobile และ Tablet ทุกประเภท | ทีมตรวจหลายคนพร้อมกัน

## 🌟 ฟีเจอร์หลัก

### 🔍 ระบบตรวจเช็ค
- ตรวจเช็ค 7 หมวดหมู่ (โครงสร้าง, ไฟฟ้า, ประปา, ประตู/หน้าต่าง, พื้น/กระเบื้อง, ความปลอดภัย, ภายนอกอาคาร)
- ถ่ายรูปเก็บหลักฐาน พร้อมบีบอัดอัตโนมัติ
- สถานะ ผ่าน ✅ / มีปัญหา 🔴 / ไม่มีรายการ ⬜ (N/A)
- เพิ่มรายการตรวจเช็คเองได้ตามต้องการ

### 👥 ระบบผู้ใช้ (Multi-User)
| บทบาท | สิทธิ์ |
|--------|--------|
| 👨‍💼 Admin | จัดการผู้ใช้ ตั้งค่าระบบ ดูข้อมูลทั้งหมด |
| 🔍 Inspector | ตรวจเช็ค ดูรายงาน แชร์รายงาน |
| 👁️ Viewer | ดูเฉพาะรายงานที่ถูกแชร์มาให้ |

### 🟣 โหมดทีมตรวจ (Team Inspection)
- สร้างทีมตรวจหลายคนสำหรับบ้านหลังเดียวกัน
- เลือกสมาชิกทีมจาก user ที่ลงทะเบียนแล้ว
- ระบบสี assigns สีแต่ละคนอัตโนมัติ (ไม่ซ้ำกัน)
- แสดงสถานะปุ่มสีตามผู้เลือกแบบ Real-time
- ซิงค์ข้อมูลทุก 5 วินาที ผ่าน team session polling

### 📊 รายงาน
- PDF หน้าปกสีขาว รูปบ้านขนาดใหญ่
- ตาราง 6 รูปต่อหน้า พร้อมรายละเอียดจุดที่แก้ไข
- ตรวจรอบ 2 (Re-inspection) - เปรียบเทียบผลลัพธ์
- Export PDF เปรียบเทียบ รอบ 1 vs รอบ 2
- Export Excel 3 ชีท (สรุป / รายละเอียด / เปรียบเทียบ)

### 🔔 แจ้งเตือน (Notifications)
- Push Notification (Browser) สำหรับสมาชิกใหม่เข้าทีม
- แจ้งเตือน inspection ใหม่ / แชร์รายงาน
- ไอkręc Bell แสดง unread count

### 📜 ประวัติและค้นหา
- ค้นหาและกรองประวัติ inspection ตามวันที่ / ชื่อเจ้าของ
- ลบรายการเดี่ยว หรือ ลบทั้งหมด
- ข้อมูลเก็บใน Google Sheets ทั้งหมด

## 📁 โครงสร้างโปรเจกต์

```
uchi-kakunin/
├── index.html          ← Frontend (GitHub Pages)
├── public/
│   └── index.html      ← Copy สำหรับ Vercel
├── api/
│   └── index.py        ← Flask API (Vercel)
├── vercel.json         ← Vercel config
├── requirements.txt    ← Python dependencies
├── README.md
└── INSTALLATION_GUIDE.md
```

## 🚀 ติดตั้งและ Deploy (สรุปย่อ)

ดูรายละเอียดทั้งหมดใน [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)

### 1. Google Sheets + Service Account
1. สร้าง Google Spreadsheet ใหม่
2. สร้าง Service Account ใน Google Cloud Console
3. เปิด Google Sheets API + Drive API
4. Share Spreadsheet ให้ Service Account (Editor)

### 2. Deploy Backend (Vercel)
1. Push โค้ดขึ้น GitHub
2. Import repo ใน Vercel
3. ตั้ง Environment Variables:
   - `GOOGLE_SHEETS_ID` — Spreadsheet ID
   - `SERVICE_ACCOUNT_JSON` — JSON credentials
   - `JWT_SECRET` — Secret key (optional)
4. Deploy อัตโนมัติ

### 3. Deploy Frontend (GitHub Pages)
1. เปิด GitHub Pages ที่ Settings → Pages → branch `main`
2. เข้าใช้งานผ่าน URL ของ GitHub Pages

### 4. ตั้งค่าแอป
1. เปิดแอป → ไปแท็บตั้งค่า
2. ใส่ API URL: `https://your-app.vercel.app/api`
3. บันทึก → สมัครสมาชิก/Admin คนแรก

## 📱 วิธีใช้งาน

### เริ่มต้นใช้งาน
1. เปิดแอปบนมือถือ/แท็บเล็ต/คอมพิวเตอร์
2. กดไอคอน 👤 → เข้าสู่ระบบ / สมัครสมาชิก
3. สมัครสมาชิกแรกเป็น Admin (หรือเปลี่ยน Role ใน Google Sheets)

### ตรวจเช็คบ้าน
1. กดแท็บ 🔍 "ตรวจเช็ค"
2. กรอกข้อมูลทรัพย์สิน (ชื่อเจ้าของ + ที่อยู่) → รายการตรวจเช็คจะแสดง
3. ถ่ายรูปหน้าบ้าน
4. เลือกหมวด → แตะ "ผ่าน" / "มีปัญหา" / N/A
5. กรณีมีปัญหา → กรอกรายละเอียด + ถ่ายรูป
6. กด **"บันทึกรายการ"** ด้านล่างสุด

### โหมดทีมตรวจ
1. เปิด ☑️ "โหมดทีมตรวจ"
2. เลือกสมาชิกทีมจาก user ที่ลงทะเบียนแล้ว
3. กด "เริ่มซิงค์ทีม" → ได้รหัสทีม
4. สมาชิกคนอื่น: เปิด ☑️ → กด "เข้าร่วมซิงค์" → ใส่รหัสทีม
5. ทุกคนจะเห็นสถานะสีเดียวกันแบบ Real-time

### ตรวจรอบ 2 (Re-inspection)
1. เปิด inspection เดิมที่มีปัญหา
2. กดปุ่ม "ตรวจรอบ 2"
3. ถ่ายรูปการแก้ไข + เลือก ผ่าน/ไม่ผ่าน
4. Export PDF เปรียบเทียบ รอบ 1 vs รอบ 2

### จัดการผู้ใช้ (Admin)
1. ไปแท็บ 👥 "ผู้ใช้"
2. เปลี่ยนบทบาท: กดปุ่ม ✏️
3. เปิด/ปิดบัญชี: กดปุ่ม ⭕/🔴
4. ลบผู้ใช้: กดปุ่ม 🗑️

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_SHEETS_ID` | ✅ | Google Spreadsheet ID |
| `SERVICE_ACCOUNT_JSON` | ✅ | JSON ของ Service Account credentials |
| `JWT_SECRET` | ❌ | Secret key สำหรับเข้ารหัส token (auto-generate ถ้าไม่ใส่) |

## 🛠️ เทคโนโลยี

| ส่วน | เทคโนโลยี |
|------|-----------|
| Frontend | HTML + Tailwind CSS + JavaScript |
| Backend | Python Flask |
| Database | Google Sheets |
| Hosting FE | GitHub Pages (ฟรี) |
| Hosting BE | Vercel (ฟรี) |

## 📄 License

MIT License
