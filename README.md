# 🏠 Uchi Kakunin Setsubi | ระบบตรวจเช็คบ้าน

ระบบเว็บแอปพลิเคชันสำหรับตรวจเช็คบ้าน พร้อมรายงานจุดที่ต้องแก้ไข รองรับ Mobile และ Tablet ทุกประเภท

## 🌟 ฟีเจอร์

- ✅ ตรวจเช็ค 7 หมวดหมู่ (โครงสร้าง, ไฟฟ้า, ประปา, ประตู/หน้าต่าง, พื้น/เพดาน, ความปลอดภัย, ภายนอก)
- ✅ รายงานสรุปจุดที่ต้องแก้ไข
- ✅ ถ่ายรูปเก็บหลักฐาน
- ✅ Responsive รองรับ Mobile & Tablet
- ✅ Dark Mode อัตโนมัติ
- ✅ Export รายงาน (พิมพ์, แชร์, JSON)
- ✅ ซิงค์ข้อมูลกับ Google Sheets
- ✅ ประวัติการตรวจเช็ค

## 🚀 ติดตั้งและ Deploy

### Frontend (GitHub Pages)

1. Push ไฟล์ `index.html` ขึ้น GitHub
2. เปิด GitHub Pages ที่ Settings → Pages → เลือก branch `main`
3. เข้าใช้งานผ่าน URL ของ GitHub Pages

### Backend (Vercel)

1. Push ไฟล์ทั้งหมดขึ้น Vercel

2. ตั้งค่า Environment Variables ใน Vercel:
   ```
   GOOGLE_SHEETS_ID=your_spreadsheet_id
   SERVICE_ACCOUNT_JSON={"type":"service_account",...}
   ```

3. Deploy อัตโนมัติ

### Google Sheets Setup

1. สร้าง Google Spreadsheet ใหม่
2. สร้าง Service Account ใน Google Cloud Console
3. เปิดสิทธิ์เข้าถึง Spreadsheet ให้ Service Account
4. คัดลอก Spreadsheet ID ไปตั้งค่าในหน้า Settings ของแอป

## 📱 วิธีใช้งาน

1. เปิดแอปบนมือถือหรือแท็บเล็ต
2. กรอกข้อมูลทรัพย์สิน
3. เลือกหมวดหมู่ที่ต้องการตรวจ
4. แตะปุ่ม "ผ่าน" หรือ "มีปัญหา" สำหรับแต่ละรายการ
5. กรณีมีปัญหา ให้กรอกรายละเอียดและถ่ายรูป
6. กด "บันทึกรายงาน" เมื่อตรวจเสร็จ
7. ดูรายงานสรุปและจุดที่ต้องแก้ไข

## 📁 โครงสร้างโปรเจกต์

```
├── index.html          # Frontend (GitHub Pages)
├── api/
│   └── index.py        # Flask API (Vercel)
├── vercel.json         # Vercel config
├── requirements.txt    # Python dependencies
└── README.md
```

## ⚙️ Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_SHEETS_ID` | Google Spreadsheet ID |
| `SERVICE_ACCOUNT_JSON` | JSON string ของ Service Account credentials |
| `SHEET_NAME` | ชื่อ Worksheet (default: InspectionData) |

## 📄 License

MIT License
