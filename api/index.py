"""
House Inspection API - Flask Backend
สำหรับ deploy บน Vercel + เชื่อมต่อ Google Sheets
รองรับ Multi-User System
"""
import os
import json
import hashlib
import hmac
import base64
import secrets
import gspread
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account as google_service_account
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

# ===== CONFIG =====
GOOGLE_SHEETS_ID = os.environ.get("GOOGLE_SHEETS_ID", "")
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not JWT_SECRET:
    # Fallback: derive from Google Sheets ID so it's stable across cold starts
    JWT_SECRET = hashlib.sha256((GOOGLE_SHEETS_ID or "uchi-kakunin-default").encode()).hexdigest()

# Sheet names
USERS_SHEET = "Users"
INSPECTION_SHEET = "InspectionData"
SHARE_SHEET = "SharedReports"
ACTIVITY_SHEET = "ActivityLog"

# ===== STATELESS TOKEN SYSTEM (HMAC-signed) =====
# ไม่ใช้ in-memory storage — ทำงานได้บน Vercel serverless

def generate_token(user_id, role, display_name=""):
    """สร้าง signed token (ไม่ต้องเก็บ server-side)"""
    payload = {
        "user_id": user_id,
        "role": role,
        "displayName": display_name,
        "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"

def verify_token(token):
    """ตรวจสอบ token จาก HMAC signature"""
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        if datetime.fromisoformat(payload["exp"]) < datetime.utcnow():
            return None
        return payload
    except Exception:
        return None

def require_auth(f):
    """Decorator สำหรับ endpoints ที่ต้อง login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user = verify_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """Decorator สำหรับ admin endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user = verify_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        if user["role"] != "admin":
            return jsonify({"error": "Forbidden - Admin only"}), 403
        request.user = user
        return f(*args, **kwargs)
    return decorated


# ===== GOOGLE SHEETS =====
def get_google_sheets_client():
    """สร้าง Google Sheets client จาก Service Account"""
    try:
        if SERVICE_ACCOUNT_JSON:
            creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
            # Fix private_key: replace literal \\n with actual newlines
            # Vercel env vars may store \\n as literal backslash-n
            if "private_key" in creds_dict:
                pk = creds_dict["private_key"]
                if "\\n" in pk and "\n" not in pk:
                    pk = pk.replace("\\n", "\n")
                    creds_dict["private_key"] = pk
        else:
            creds_file = os.path.join(os.path.dirname(__file__), "service_account.json")
            if not os.path.exists(creds_file):
                print("SERVICE_ACCOUNT_JSON not set and no service_account.json found")
                return None
            with open(creds_file) as f:
                creds_dict = json.load(f)

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = google_service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scope
        )
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Sheets connection error: {type(e).__name__}: {e}")
        return None

def get_or_create_worksheet(client, sheet_name, headers=None):
    """ดึงหรือสร้าง worksheet"""
    if not GOOGLE_SHEETS_ID:
        return None
    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=25)
            if headers:
                worksheet.update("A1", [headers])
                worksheet.format(f"A1:{chr(64+len(headers))}1", {"textFormat": {"bold": True}})
        return worksheet
    except Exception as e:
        print(f"Worksheet error: {e}")
        return None

def safe_get_all_records(ws):
    """Get all records safely - handles empty sheets"""
    try:
        rows = ws.get_all_values()
        if len(rows) < 2:
            return []
        headers = rows[0]
        records = []
        for row in rows[1:]:
            record = {}
            for i, h in enumerate(headers):
                if h:
                    record[h] = row[i] if i < len(row) else ""
            records.append(record)
        return records
    except Exception:
        return []


def log_activity(user_id, action, details=""):
    """บันทึก activity log"""
    try:
        client = get_google_sheets_client()
        if not client:
            return
        ws = get_or_create_worksheet(client, ACTIVITY_SHEET, [
            "Timestamp", "UserID", "Action", "Details"
        ])
        if ws:
            ws.append_row([
                datetime.now().isoformat(),
                user_id,
                action,
                details
            ], value_input_option="USER_ENTERED")
    except:
        pass


# ===== SERVE FRONTEND =====
from flask import send_from_directory

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """serve index.html สำหรับทุก non-API route"""
    if path.startswith("api"):
        return jsonify({"error": "Not found"}), 404
    pub_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public")
    return send_from_directory(pub_dir, "index.html")


# ===== AUTH ROUTES =====

@app.route("/api/auth/register", methods=["POST"])
def register():
    """สมัครสมาชิก"""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        display_name = data.get("displayName", "").strip()
        role = data.get("role", "inspector")  # admin, inspector, viewer

        if not username or not password:
            return jsonify({"error": "กรุณากรอก username และ password"}), 400

        if len(password) < 4:
            return jsonify({"error": "Password ต้องมีอย่างน้อย 4 ตัวอักษร"}), 400

        client = get_google_sheets_client()
        if not client:
            print(f"[REGISTER] Google Sheets unavailable for {username}")
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - กรุณาลองใหม่ภายหลัง"}), 503

        ws = get_or_create_worksheet(client, USERS_SHEET, [
            "UserID", "Username", "PasswordHash", "DisplayName",
            "Role", "CreatedAt", "LastLogin", "Active"
        ])
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - กรุณาลองใหม่ภายหลัง"}), 503

        # Check duplicate
        try:
            records = safe_get_all_records(ws)
        except Exception:
            records = []
        for r in records:
            if r.get("Username") == username and (r.get("Active") or "").lower() == "true":
                return jsonify({"error": "Username นี้ถูกใช้แล้ว"}), 400

        # Create user
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        ws.append_row([
            user_id, username, password_hash, display_name or username,
            role, datetime.now().isoformat(), "", "true"
        ], value_input_option="USER_ENTERED")

        # Generate token
        token = generate_token(user_id, role, display_name or username)

        log_activity(user_id, "register", f"User {username} registered")

        return jsonify({
            "status": "ok",
            "token": token,
            "user": {
                "id": user_id,
                "username": username,
                "displayName": display_name or username,
                "role": role
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    """เข้าสู่ระบบ"""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "กรุณากรอก username และ password"}), 400

        client = get_google_sheets_client()
        if not client:
            print(f"[LOGIN] Google Sheets unavailable for {username}")
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - กรุณาลองใหม่ภายหลัง"}), 503

        ws = get_or_create_worksheet(client, USERS_SHEET)
        if not ws:
            print(f"[LOGIN] Users sheet not found for {username}")
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - กรุณาลองใหม่ภายหลัง"}), 503

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            records = safe_get_all_records(ws)
        except Exception:
            records = []

        for r in records:
            if (r.get("Username") == username and
                r.get("PasswordHash") == password_hash and
                (r.get("Active") or "").lower() == "true"):

                user_id = r["UserID"]
                role = r.get("Role", "inspector")
                display_name = r.get("DisplayName", username)

                token = generate_token(user_id, role, display_name)

                # Update last login
                try:
                    cell = ws.find(user_id)
                    if cell:
                        ws.update_cell(cell.row, 7, datetime.now().isoformat())
                except:
                    pass

                log_activity(user_id, "login", f"{username} logged in")

                return jsonify({
                    "status": "ok",
                    "token": token,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "displayName": display_name,
                        "role": role
                    }
                })

        return jsonify({"error": "Username หรือ Password ไม่ถูกต้อง"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_me():
    """ดึงข้อมูลผู้ใช้ปัจจุบัน (ใช้ข้อมูลจาก token)"""
    user = request.user
    return jsonify({
        "status": "ok",
        "user": {
            "id": user["user_id"],
            "username": user.get("user_id", ""),
            "displayName": user.get("displayName", ""),
            "role": user.get("role", "inspector")
        }
    })


@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    """ออกจากระบบ (stateless token - ลบฝั่ง client)"""
    return jsonify({"status": "ok", "message": "Logged out"})


# ===== USER MANAGEMENT (Admin) =====

@app.route("/api/users", methods=["GET"])
@require_admin
def get_users():
    """ดึงรายชื่อผู้ใช้ทั้งหมด (Admin)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - Google Sheets ไม่เชื่อมต่อ"}), 503

        ws = get_or_create_worksheet(client, USERS_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน - Google Sheets ไม่เชื่อมต่อ"}), 503

        try:
            records = safe_get_all_records(ws)
        except Exception:
            records = []
        users = []
        for r in records:
            uid = r.get("UserID", "")
            if not uid:
                continue
            # แสดงเฉพาะ user ที่ Active (ไม่แสดง user ที่ถูกลบ/ปิดใช้งาน)
            active_val = (r.get("Active") or "true")
            if str(active_val).lower() == "false":
                continue
            users.append({
                "id": uid,
                "username": r.get("Username", ""),
                "displayName": r.get("DisplayName", ""),
                "role": r.get("Role", "inspector"),
                "active": True,
                "createdAt": r.get("CreatedAt", ""),
                "lastLogin": r.get("LastLogin", "")
            })

        return jsonify({"status": "ok", "users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<user_id>", methods=["PUT"])
@require_admin
def update_user(user_id):
    """อัปเดตข้อมูลผู้ใช้ (Admin)"""
    try:
        data = request.get_json()
        client = get_google_sheets_client()
        if not client:
            return jsonify({"status": "ok", "message": "Offline mode"})

        ws = get_or_create_worksheet(client, USERS_SHEET)
        if not ws:
            return jsonify({"status": "ok", "message": "Offline mode"})

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("UserID") == user_id:
                if "role" in data:
                    ws.update_cell(idx, 5, data["role"])
                if "displayName" in data:
                    ws.update_cell(idx, 4, data["displayName"])
                if "active" in data:
                    ws.update_cell(idx, 8, "true" if data["active"] else "false")

                log_activity(request.user["user_id"], "update_user", f"Updated user {user_id}")
                return jsonify({"status": "ok", "message": "User updated"})

        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500@app.route("/api/users/<user_id>", methods=["DELETE"])
@require_admin
def delete_user(user_id):
    """ลบผู้ใช้ออกจากระบบ (Hard delete - ลบออกจาก Google Sheets)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, USERS_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("UserID") == user_id:
                # ป้องกันลบตัวเอง
                if user_id == request.user["user_id"]:
                    return jsonify({"error": "ไม่สามารถลบตัวเองได้"}), 400
                # Hard delete - ลบ row ออกจาก Google Sheets
                ws.delete_rows(idx)
                log_activity(request.user["user_id"], "delete_user", f"Deleted user {user_id} from Google Sheets")
                return jsonify({"status": "ok", "message": "ลบผู้ใช้สำเร็จ"})

        return jsonify({"error": "ไม่พบผู้ใช้"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== SHARING =====

@app.route("/api/share", methods=["POST"])
@require_auth
def share_report():
    """แชร์รายงานให้ผู้ใช้อื่น"""
    try:
        data = request.get_json()
        inspection_id = data.get("inspectionId")
        share_with = data.get("shareWith")  # user_id or "all"
        permission = data.get("permission", "view")  # view, edit

        if not inspection_id:
            return jsonify({"error": "Inspection ID required"}), 400

        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, SHARE_SHEET, [
            "ShareID", "InspectionID", "SharedBy", "ShareWith",
            "Permission", "CreatedAt"
        ])
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        share_id = f"share_{secrets.token_hex(8)}"
        ws.append_row([
            share_id, inspection_id, request.user["user_id"],
            share_with, permission, datetime.now().isoformat()
        ], value_input_option="USER_ENTERED")

        log_activity(request.user["user_id"], "share", f"Shared {inspection_id} with {share_with}")

        # Create notification
        try:
            target_users = []
            if share_with == "all":
                users_ws = get_or_create_worksheet(client, USERS_SHEET)
                if users_ws:
                    for ur in safe_get_all_records(users_ws):
                        if (ur.get("Active") or "").lower() == "true" and ur.get("UserID") != request.user["user_id"]:
                            target_users.append(ur["UserID"])
            else:
                target_users = [share_with]

            ws_notif = get_or_create_worksheet(client, NOTIFICATION_SHEET, [
                "NotifID", "UserID", "Type", "Title", "Message", "Link", "Read", "CreatedAt"
            ])
            if ws_notif:
                for uid in target_users:
                    notif_id = f"notif_{secrets.token_hex(8)}"
                    ws_notif.append_row([
                        notif_id, uid, "shared_report",
                        "🔗 มีรายงานถูกแชร์มาให้",
                        f"มีรายงานการตรวจเช็คถูกแชร์มาให้คุณ (ID: {inspection_id})",
                        str(inspection_id), "false", datetime.now().isoformat()
                    ], value_input_option="USER_ENTERED")
        except:
            pass

        return jsonify({"status": "ok", "shareId": share_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/share/shared-with-me", methods=["GET"])
@require_auth
def get_shared_with_me():
    """ดึงรายงานที่ถูกแชร์มาให้"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"shared": []})

        ws = get_or_create_worksheet(client, SHARE_SHEET)
        if not ws:
            return jsonify({"shared": []})

        records = safe_get_all_records(ws)
        shared = []

        # Also get inspection data for context
        inspection_ws = get_or_create_worksheet(client, INSPECTION_SHEET)
        inspection_map = {}
        if inspection_ws:
            try:
                for ir in safe_get_all_records(inspection_ws):
                    if ir.get("Raw JSON"):
                        insp = json.loads(ir["Raw JSON"])
                        inspection_map[str(ir.get("InspectionID", insp.get("id", "")))] = insp
            except:
                pass

        for r in records:
            if r.get("ShareWith") in [request.user["user_id"], "all"]:
                insp_id = r.get("InspectionID", "")
                insp_data = inspection_map.get(str(insp_id), {})
                shared.append({
                    "shareId": r.get("ShareID"),
                    "inspectionId": insp_id,
                    "sharedBy": r.get("SharedBy"),
                    "permission": r.get("Permission"),
                    "createdAt": r.get("CreatedAt"),
                    "ownerName": insp_data.get("ownerName", ""),
                    "address": insp_data.get("address", ""),
                    "date": insp_data.get("date", ""),
                    "inspectorName": insp_data.get("inspectorName", ""),
                    "isReinspection": insp_data.get("isReinspection", False),
                    "summary": insp_data.get("summary", {})
                })

        return jsonify({"status": "ok", "shared": shared})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== INSPECTIONS (with user context) =====

@app.route("/api", methods=["GET"])
def api_index():
    """Health check"""
    return jsonify({
        "status": "ok",
        "message": "House Inspection API",
        "version": "2.0.0 (Multi-User)",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/inspections", methods=["GET"])
@require_auth
def get_inspections():
    """ดึงรายการตรวจ (เฉพาะของตัวเอง + ที่ถูกแชร์)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "Google Sheets not configured", "inspections": []}), 200

        ws = get_or_create_worksheet(client, INSPECTION_SHEET)
        if not ws:
            return jsonify({"error": "Cannot access spreadsheet", "inspections": []}), 200

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        user_role = request.user["role"]

        # Get shared inspection IDs
        shared_ids = set()
        try:
            share_ws = get_or_create_worksheet(client, SHARE_SHEET)
            if share_ws:
                share_records = safe_get_all_records(share_ws)
                for sr in share_records:
                    if sr.get("ShareWith") in [user_id, "all"]:
                        shared_ids.add(str(sr.get("InspectionID")))
        except:
            pass

        inspections = []
        for record in records:
            if record.get("Raw JSON"):
                try:
                    inspection = json.loads(record["Raw JSON"])
                    owner = inspection.get("userId", "")

                    # Admin sees all, others see own + shared
                    if user_role == "admin" or owner == user_id or str(inspection.get("id")) in shared_ids:
                        inspection["_owner"] = owner
                        inspections.append(inspection)
                except json.JSONDecodeError:
                    pass

        return jsonify({
            "status": "ok",
            "count": len(inspections),
            "inspections": inspections
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inspections", methods=["POST"])
@require_auth
def create_inspection():
    """บันทึกผลตรวจใหม่"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Add user info
        data["userId"] = request.user["user_id"]
        data["userName"] = request.user.get("displayName", "")

        # นับผลตรวจ
        check_data = data.get("data", {})
        pass_count = sum(1 for v in check_data.values() if v.get("status") == "pass")
        fail_count = sum(1 for v in check_data.values() if v.get("status") == "fail")
        total = pass_count + fail_count

        # สรุปรายละเอียดปัญหา
        issues = []
        for key, val in check_data.items():
            if val.get("status") == "fail":
                if isinstance(val, dict) and val.get("issues"):
                    for issue in val["issues"]:
                        issues.append(f"{key}: {issue.get('note', 'ไม่มีรายละเอียด')}")
                else:
                    issues.append(f"{key}: {val.get('note', 'ไม่มีรายละเอียด')}")

        row = [
            data.get("id", ""),
            data.get("date", ""),
            data.get("ownerName", ""),
            data.get("address", ""),
            data.get("houseType", ""),
            data.get("inspectorName", ""),
            f"{pass_count}/{total}",
            pass_count,
            fail_count,
            "\n".join(issues),
            data.get("timestamp", datetime.now().isoformat()),
            request.user["user_id"],
            json.dumps(data, ensure_ascii=False)
        ]

        # บันทึกลง Google Sheets
        client = get_google_sheets_client()
        if client:
            ws = get_or_create_worksheet(client, INSPECTION_SHEET, [
                "ID", "วันที่ตรวจ", "ชื่อเจ้าของ", "ที่อยู่", "ประเภทบ้าน",
                "ชื่อผู้ตรวจ", "คะแนนรวม", "รายการผ่าน", "รายการปัญหา",
                "รายละเอียดปัญหา", "Timestamp", "UserID", "Raw JSON"
            ])
            if ws:
                ws.append_row(row, value_input_option="USER_ENTERED")

        # บันทึกลงไฟล์ local (backup)
        save_local_backup(data)

        log_activity(request.user["user_id"], "create_inspection", f"Inspection {data.get('id')}")

        # Create notification for admin users
        try:
            users_ws = get_or_create_worksheet(client, USERS_SHEET)
            if users_ws:
                user_records = safe_get_all_records(users_ws)
                for ur in user_records:
                    if ur.get("Role") == "admin" and ur.get("UserID") != request.user["user_id"] and (ur.get("Active") or "").lower() == "true":
                        notif_id = f"notif_{secrets.token_hex(8)}"
                        ws_notif = get_or_create_worksheet(client, NOTIFICATION_SHEET, [
                            "NotifID", "UserID", "Type", "Title", "Message", "Link", "Read", "CreatedAt"
                        ])
                        if ws_notif:
                            ws_notif.append_row([
                                notif_id, ur["UserID"], "new_inspection",
                                "📋 รายงานตรวจใหม่",
                                f"{request.user.get('displayName', 'User')} บันทึกรายการตรวจ {data.get('ownerName', '')} - {data.get('address', '')}",
                                str(data.get("id")), "false", datetime.now().isoformat()
                            ], value_input_option="USER_ENTERED")
        except:
            pass

        return jsonify({
            "status": "ok",
            "message": "Inspection saved successfully",
            "id": data.get("id")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inspections/<inspection_id>", methods=["GET"])
@require_auth
def get_inspection(inspection_id):
    """ดึงผลตรวจรายการเดียว"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "Inspection not found"}), 404

        ws = get_or_create_worksheet(client, INSPECTION_SHEET)
        if not ws:
            return jsonify({"error": "Inspection not found"}), 404

        records = safe_get_all_records(ws)
        for record in records:
            if str(record.get("ID")) == str(inspection_id):
                if record.get("Raw JSON"):
                    inspection = json.loads(record["Raw JSON"])
                    # Check permission
                    owner = inspection.get("userId", "")
                    if owner == request.user["user_id"] or request.user["role"] == "admin":
                        return jsonify(inspection)
                    return jsonify({"error": "Access denied"}), 403

        return jsonify({"error": "Inspection not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inspections/<inspection_id>", methods=["DELETE"])
@require_auth
def delete_inspection(inspection_id):
    """ลบผลตรวจ"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"status": "ok", "message": "Offline mode"})

        ws = get_or_create_worksheet(client, INSPECTION_SHEET)
        if not ws:
            return jsonify({"status": "ok", "message": "Offline mode"})

        records = safe_get_all_records(ws)
        for idx, record in enumerate(records, start=2):
            if str(record.get("ID")) == str(inspection_id):
                # Check permission
                if record.get("UserID") == request.user["user_id"] or request.user["role"] == "admin":
                    ws.delete_rows(idx)
                    log_activity(request.user["user_id"], "delete_inspection", f"Deleted {inspection_id}")
                    return jsonify({"status": "ok", "message": "Deleted"})
                return jsonify({"error": "Access denied"}), 403

        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
@require_auth
def get_stats():
    """ดึงสถิติ"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"total_inspections": 0, "total_issues": 0})

        ws = get_or_create_worksheet(client, INSPECTION_SHEET)
        if not ws:
            return jsonify({"total_inspections": 0, "total_issues": 0})

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        user_role = request.user["role"]

        my_inspections = 0
        total_issues = 0
        for r in records:
            owner = r.get("UserID", "")
            if user_role == "admin" or owner == user_id:
                my_inspections += 1
                total_issues += int(r.get("รายการปัญหา", 0))

        return jsonify({
            "total_inspections": my_inspections,
            "total_issues": total_issues,
            "role": user_role
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== NOTIFICATIONS =====

NOTIFICATION_SHEET = "Notifications"

@app.route("/api/notifications", methods=["GET"])
@require_auth
def get_notifications():
    """ดึงการแจ้งเตือนของ user"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"notifications": [], "unread": 0})

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET, [
            "NotifID", "UserID", "Type", "Title", "Message", "Link", "Read", "CreatedAt"
        ])
        if not ws:
            return jsonify({"notifications": [], "unread": 0})

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        notifications = []
        unread = 0
        for r in records:
            if r.get("UserID") == user_id:
                is_read = (r.get("Read") or "").lower() == "true"
                if not is_read:
                    unread += 1
                notifications.append({
                    "id": r.get("NotifID"),
                    "type": r.get("Type"),
                    "title": r.get("Title"),
                    "message": r.get("Message"),
                    "link": r.get("Link"),
                    "read": is_read,
                    "createdAt": r.get("CreatedAt")
                })

        # Sort by date desc
        notifications.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        notifications = notifications[:50]  # Limit to 50

        return jsonify({"status": "ok", "notifications": notifications, "unread": unread})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _create_notification_internal(target_user_id, notif_type, title, message, link=""):
    """สร้าง notification โดยไม่ต้องมี auth (ใช้ภายใน)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET, [
            "NotifID", "UserID", "Type", "Title", "Message", "Link", "Read", "CreatedAt"
        ])
        if not ws:
            return False

        notif_id = f"notif_{secrets.token_hex(8)}"
        ws.append_row([
            notif_id, target_user_id, notif_type, title, message,
            link, "false", datetime.now().isoformat()
        ], value_input_option="USER_ENTERED")
        return True
    except Exception:
        return False


@app.route("/api/notifications", methods=["POST"])
@require_auth
def create_notification():
    """สร้างการแจ้งเตือน"""
    try:
        data = request.get_json()
        target_user = data.get("userId", request.user["user_id"])
        notif_type = data.get("type", "info")
        title = data.get("title", "")
        message = data.get("message", "")
        link = data.get("link", "")

        client = get_google_sheets_client()
        if not client:
            notif_id = f"notif_{secrets.token_hex(8)}"
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET, [
            "NotifID", "UserID", "Type", "Title", "Message", "Link", "Read", "CreatedAt"
        ])
        if not ws:
            notif_id = f"notif_{secrets.token_hex(8)}"
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        notif_id = f"notif_{secrets.token_hex(8)}"
        ws.append_row([
            notif_id, target_user, notif_type, title, message,
            link, "false", datetime.now().isoformat()
        ], value_input_option="USER_ENTERED")

        return jsonify({"status": "ok", "notifId": notif_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notifications/read-all", methods=["PUT"])
@require_auth
def mark_all_read():
    """ทำเครื่องหมายว่าอ่านทั้งหมด"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        count = 0
        for idx, r in enumerate(records, start=2):
            if r.get("UserID") == user_id and r.get("Read") != "true":
                ws.update_cell(idx, 7, "true")
                count += 1

        return jsonify({"status": "ok", "marked": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notifications/<notif_id>/read", methods=["PUT"])
@require_auth
def mark_notification_read(notif_id):
    """ทำเครื่องหมายว่าอ่านแล้ว"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("NotifID") == notif_id and r.get("UserID") == request.user["user_id"]:
                ws.update_cell(idx, 7, "true")
                return jsonify({"status": "ok"})

        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notifications/unread-count", methods=["GET"])
@require_auth
def get_unread_count():
    """ดึงจำนวน unread"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"unread": 0})

        ws = get_or_create_worksheet(client, NOTIFICATION_SHEET)
        if not ws:
            return jsonify({"unread": 0})

        records = safe_get_all_records(ws)
        unread = sum(1 for r in records if r.get("UserID") == request.user["user_id"] and r.get("Read") != "true")

        return jsonify({"status": "ok", "unread": unread})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== CUSTOM CHECKLIST ITEMS =====

CUSTOM_ITEMS_SHEET = "CustomChecklistItems"

@app.route("/api/custom-items", methods=["GET"])
@require_auth
def get_custom_items():
    """ดึงรายการตรวจสอบที่เพิ่มเอง"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"customItems": {}})

        ws = get_or_create_worksheet(client, CUSTOM_ITEMS_SHEET, [
            "UserID", "SectionID", "ItemID", "Text", "CreatedAt"
        ])
        if not ws:
            return jsonify({"customItems": {}})

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        items = {}
        for r in records:
            if r.get("UserID") == user_id:
                section = r.get("SectionID", "")
                if section not in items:
                    items[section] = []
                items[section].append({
                    "id": r.get("ItemID"),
                    "text": r.get("Text")
                })

        return jsonify({"status": "ok", "customItems": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/custom-items", methods=["POST"])
@require_auth
def save_custom_items():
    """บันทึกรายการตรวจสอบที่เพิ่มเอง (bulk save)"""
    try:
        data = request.get_json()
        items = data.get("items", {})  # { sectionId: [{id, text}] }

        client = get_google_sheets_client()
        if not client:
            count = sum(len(v) for v in items.values())
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, CUSTOM_ITEMS_SHEET, [
            "UserID", "SectionID", "ItemID", "Text", "CreatedAt"
        ])
        if not ws:
            count = sum(len(v) for v in items.values())
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        user_id = request.user["user_id"]

        # Delete existing items for this user
        records = safe_get_all_records(ws)
        rows_to_delete = []
        for idx, r in enumerate(records, start=2):
            if r.get("UserID") == user_id:
                rows_to_delete.append(idx)
        # Delete in reverse order to maintain indices
        for idx in reversed(rows_to_delete):
            ws.delete_rows(idx)

        # Insert new items
        count = 0
        for section_id, section_items in items.items():
            for item in section_items:
                ws.append_row([
                    user_id, section_id, item.get("id", ""),
                    item.get("text", ""), datetime.now().isoformat()
                ], value_input_option="USER_ENTERED")
                count += 1

        log_activity(user_id, "save_custom_items", f"Saved {count} custom items")
        return jsonify({"status": "ok", "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/custom-items/<item_id>", methods=["DELETE"])
@require_auth
def delete_custom_item(item_id):
    """ลบรายการตรวจสอบที่เพิ่มเอง"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"status": "ok", "message": "Offline mode"})

        ws = get_or_create_worksheet(client, CUSTOM_ITEMS_SHEET)
        if not ws:
            return jsonify({"status": "ok", "message": "Offline mode"})

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]

        for idx, r in enumerate(records, start=2):
            if r.get("ItemID") == item_id and r.get("UserID") == user_id:
                ws.delete_rows(idx)
                return jsonify({"status": "ok", "message": "Deleted"})

        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== OFFLINE SYNC QUEUE =====

SYNC_QUEUE_SHEET = "SyncQueue"

@app.route("/api/sync-queue", methods=["POST"])
@require_auth
def add_to_sync_queue():
    """Sync queue for pending operations"""
    try:
        data = request.get_json()
        action = data.get("action")  # create_inspection, save_custom_items, etc.
        payload = data.get("payload", {})

        client = get_google_sheets_client()
        if not client:
            queue_id = f"q_{secrets.token_hex(8)}"
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, SYNC_QUEUE_SHEET, [
            "QueueID", "UserID", "Action", "Payload", "Status", "CreatedAt", "ProcessedAt"
        ])
        if not ws:
            queue_id = f"q_{secrets.token_hex(8)}"
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        queue_id = f"q_{secrets.token_hex(8)}"
        ws.append_row([
            queue_id, request.user["user_id"], action,
            json.dumps(payload, ensure_ascii=False),
            "pending", datetime.now().isoformat(), ""
        ], value_input_option="USER_ENTERED")

        return jsonify({"status": "ok", "queueId": queue_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync-queue/process", methods=["POST"])
@require_auth
def process_sync_queue():
    """ประมวลผล sync queue ทั้งหมดของ user"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, SYNC_QUEUE_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        processed = 0
        errors = 0

        for idx, r in enumerate(records, start=2):
            if r.get("UserID") == user_id and r.get("Status") == "pending":
                action = r.get("Action", "")
                try:
                    payload = json.loads(r.get("Payload", "{}"))

                    if action == "create_inspection":
                        # Process inspection creation
                        payload["userId"] = user_id
                        check_data = payload.get("data", {})
                        pass_count = sum(1 for v in check_data.values() if v.get("status") == "pass")
                        fail_count = sum(1 for v in check_data.values() if v.get("status") == "fail")

                        insp_ws = get_or_create_worksheet(client, INSPECTION_SHEET, [
                            "ID", "วันที่ตรวจ", "ชื่อเจ้าของ", "ที่อยู่", "ประเภทบ้าน",
                            "ชื่อผู้ตรวจ", "คะแนนรวม", "รายการผ่าน", "รายการปัญหา",
                            "รายละเอียดปัญหา", "Timestamp", "UserID", "Raw JSON"
                        ])
                        if insp_ws:
                            insp_ws.append_row([
                                payload.get("id", ""), payload.get("date", ""),
                                payload.get("ownerName", ""), payload.get("address", ""),
                                payload.get("houseType", ""), payload.get("inspectorName", ""),
                                f"{pass_count}/{pass_count+fail_count}", pass_count, fail_count,
                                "", payload.get("timestamp", datetime.now().isoformat()),
                                user_id, json.dumps(payload, ensure_ascii=False)
                            ], value_input_option="USER_ENTERED")
                        processed += 1

                    elif action == "save_custom_items":
                        # Process custom items save
                        custom_ws = get_or_create_worksheet(client, CUSTOM_ITEMS_SHEET, [
                            "UserID", "SectionID", "ItemID", "Text", "CreatedAt"
                        ])
                        if custom_ws:
                            # Delete existing
                            c_records = safe_get_all_records(custom_ws)
                            for ci, cr in enumerate(c_records, start=2):
                                if cr.get("UserID") == user_id:
                                    custom_ws.delete_rows(ci)
                            # Insert new
                            for section_id, section_items in payload.get("items", {}).items():
                                for item in section_items:
                                    custom_ws.append_row([
                                        user_id, section_id, item.get("id", ""),
                                        item.get("text", ""), datetime.now().isoformat()
                                    ], value_input_option="USER_ENTERED")
                        processed += 1

                    elif action == "share_report":
                        share_ws = get_or_create_worksheet(client, SHARE_SHEET, [
                            "ShareID", "InspectionID", "SharedBy", "ShareWith",
                            "Permission", "CreatedAt"
                        ])
                        if share_ws:
                            share_ws.append_row([
                                f"share_{secrets.token_hex(8)}", payload.get("inspectionId", ""),
                                user_id, payload.get("shareWith", "all"),
                                payload.get("permission", "view"), datetime.now().isoformat()
                            ], value_input_option="USER_ENTERED")
                        processed += 1

                    # Mark as processed
                    ws.update_cell(idx, 5, "done")
                    ws.update_cell(idx, 7, datetime.now().isoformat())

                except Exception as e:
                    ws.update_cell(idx, 5, f"error: {str(e)[:50]}")
                    errors += 1

        log_activity(user_id, "process_sync_queue", f"Processed: {processed}, Errors: {errors}")
        return jsonify({"status": "ok", "processed": processed, "errors": errors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync-queue", methods=["GET"])
@require_auth
def get_sync_queue():
    """ดึง sync queue ของ user"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"queue": []})

        ws = get_or_create_worksheet(client, SYNC_QUEUE_SHEET)
        if not ws:
            return jsonify({"queue": []})

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        queue = []
        for r in records:
            if r.get("UserID") == user_id:
                queue.append({
                    "queueId": r.get("QueueID"),
                    "action": r.get("Action"),
                    "status": r.get("Status"),
                    "createdAt": r.get("CreatedAt"),
                    "processedAt": r.get("ProcessedAt")
                })

        return jsonify({"status": "ok", "queue": queue})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== TEAM SESSION (Real-time Collaboration) =====

TEAM_SESSION_SHEET = "TeamSessions"

@app.route("/api/team-sessions", methods=["POST"])
@require_auth
def create_team_session():
    """สร้าง team session ใหม่ สำหรับการตรวจร่วม"""
    try:
        data = request.get_json()
        session_id = f"team_{secrets.token_hex(8)}"
        owner_name = data.get("ownerName", "")
        address = data.get("address", "")
        members = data.get("members", [])  # [{userId, displayName}]

        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET, [
            "SessionID", "OwnerUserID", "OwnerName", "Address",
            "Members", "Status", "CurrentData", "LastUpdate",
            "CreatedAt", "HousePhotos"
        ])
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws.append_row([
            session_id,
            request.user["user_id"],
            owner_name,
            address,
            json.dumps(members, ensure_ascii=False),
            "active",
            json.dumps(data.get("initialData", {}), ensure_ascii=False),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(data.get("housePhotos", []), ensure_ascii=False)
        ], value_input_option="USER_ENTERED")

        log_activity(request.user["user_id"], "create_team_session", f"Session {session_id}")
        return jsonify({"status": "ok", "sessionId": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/<session_id>", methods=["PUT"])
@require_auth
def update_team_session(session_id):
    """อัปเดตข้อมูล team session (polled by team members)"""
    try:
        data = request.get_json()

        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("SessionID") == session_id:
                # Update current data
                if "currentData" in data:
                    ws.update_cell(idx, 7, json.dumps(data["currentData"], ensure_ascii=False))
                if "housePhotos" in data:
                    ws.update_cell(idx, 10, json.dumps(data["housePhotos"], ensure_ascii=False))
                # Update property info
                if "ownerName" in data:
                    ws.update_cell(idx, 3, data["ownerName"])
                if "address" in data:
                    ws.update_cell(idx, 4, data["address"])
                if "members" in data:
                    ws.update_cell(idx, 5, json.dumps(data["members"], ensure_ascii=False))
                # Always update timestamp
                ws.update_cell(idx, 8, datetime.now().isoformat())

                return jsonify({"status": "ok"})

        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/<session_id>", methods=["GET"])
@require_auth
def get_team_session(session_id):
    """ดึงข้อมูล team session ล่าสุด (polling)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "Offline"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "Offline"}), 503

        records = safe_get_all_records(ws)
        for r in records:
            if r.get("SessionID") == session_id:
                current_data = {}
                house_photos = []
                try:
                    current_data = json.loads(r.get("CurrentData", "{}"))
                except: pass
                try:
                    house_photos = json.loads(r.get("HousePhotos", "[]"))
                except: pass
                members = []
                try:
                    members = json.loads(r.get("Members", "[]"))
                except: pass

                return jsonify({
                    "status": "ok",
                    "session": {
                        "sessionId": r.get("SessionID"),
                        "ownerUserId": r.get("OwnerUserID"),
                        "ownerName": r.get("OwnerName"),
                        "address": r.get("Address"),
                        "members": members,
                        "sessionStatus": r.get("Status"),
                        "currentData": current_data,
                        "lastUpdate": r.get("LastUpdate"),
                        "housePhotos": house_photos
                    }
                })

        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/<session_id>/join", methods=["POST"])
@require_auth
def join_team_session(session_id):
    """เข้าร่วม team session"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("SessionID") == session_id:
                members = []
                try:
                    members = json.loads(r.get("Members", "[]"))
                except: pass

                user_id = request.user["user_id"]
                display_name = request.user.get("displayName", user_id)

                # Check if already in team
                already = any(m.get("userId") == user_id for m in members)
                if not already:
                    members.append({"userId": user_id, "displayName": display_name})
                    ws.update_cell(idx, 5, json.dumps(members, ensure_ascii=False))
                    ws.update_cell(idx, 8, datetime.now().isoformat())

                    # Send push notification to ALL existing team members
                    owner_name = r.get("OwnerName", "")
                    address = r.get("Address", "")
                    existing_member_ids = [m.get("userId") for m in members if m.get("userId") and m.get("userId") != user_id]
                    for member_id in existing_member_ids:
                        _create_notification_internal(
                            target_user_id=member_id,
                            notif_type="team_member_joined",
                            title="👥 สมาชิกใหม่เข้าทีม",
                            message=f"{display_name} เข้าร่วมทีมตรวจที่ {address or owner_name} แล้ว",
                            link=f"team:{session_id}"
                        )

                return jsonify({"status": "ok", "message": "Joined team"})

        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions", methods=["GET"])
@require_auth
def list_team_sessions():
    """ดึง team sessions ทั้งหมดที่ user เป็นสมาชิก"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        user_role = request.user["role"]

        sessions = []
        for r in records:
            if r.get("Status") == "active":
                members = []
                try:
                    members = json.loads(r.get("Members", "[]"))
                except: pass
                is_member = (r.get("OwnerUserID") == user_id or
                            any(m.get("userId") == user_id for m in members))
                if is_member or user_role == "admin":
                    sessions.append({
                        "sessionId": r.get("SessionID"),
                        "ownerName": r.get("OwnerName"),
                        "address": r.get("Address"),
                        "members": members,
                        "lastUpdate": r.get("LastUpdate"),
                        "createdAt": r.get("CreatedAt")
                    })

        return jsonify({"status": "ok", "sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/<session_id>/complete", methods=["POST"])
@require_auth
def complete_team_session(session_id):
    """ปิด team session และบันทึกเป็น inspection"""
    try:
        data = request.get_json() or {}

        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        for idx, r in enumerate(records, start=2):
            if r.get("SessionID") == session_id:
                ws.update_cell(idx, 6, "completed")  # Status
                ws.update_cell(idx, 8, datetime.now().isoformat())

                # Save as inspection
                inspection_data = data.get("inspection", {})
                if inspection_data:
                    insp_ws = get_or_create_worksheet(client, INSPECTION_SHEET, [
                        "ID", "วันที่ตรวจ", "ชื่อเจ้าของ", "ที่อยู่", "ประเภทบ้าน",
                        "ชื่อผู้ตรวจ", "คะแนนรวม", "รายการผ่าน", "รายการปัญหา",
                        "รายละเอียดปัญหา", "Timestamp", "UserID", "Raw JSON"
                    ])
                    if insp_ws:
                        check = inspection_data.get("data", {})
                        pass_c = sum(1 for v in check.values() if v.get("status") == "pass")
                        fail_c = sum(1 for v in check.values() if v.get("status") == "fail")
                        insp_ws.append_row([
                            inspection_data.get("id", str(int(datetime.now().timestamp() * 1000))),
                            inspection_data.get("date", ""),
                            inspection_data.get("ownerName", r.get("OwnerName", "")),
                            inspection_data.get("address", r.get("Address", "")),
                            inspection_data.get("houseType", ""),
                            inspection_data.get("inspectorName", ""),
                            f"{pass_c}/{pass_c+fail_c}", pass_c, fail_c, "",
                            datetime.now().isoformat(),
                            request.user["user_id"],
                            json.dumps(inspection_data, ensure_ascii=False)
                        ], value_input_option="USER_ENTERED")

                log_activity(request.user["user_id"], "complete_team_session", f"Session {session_id}")
                return jsonify({"status": "ok"})

        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/<session_id>/delete", methods=["POST"])
@app.route("/api/team-sessions/<session_id>", methods=["DELETE"])
@require_auth
def delete_team_session(session_id):
    """ลบ team session - สำหรับ owner หรือ admin เท่านั้น"""
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        user_id = request.user["user_id"]
        user_role = request.user["role"]

        for idx, r in enumerate(records, start=2):
            if r.get("SessionID") == session_id:
                # Only owner or admin can delete
                if r.get("OwnerUserID") != user_id and user_role != "admin":
                    return jsonify({"error": "ไม่มีสิทธิ์ลบ session นี้"}), 403

                # Delete row from Google Sheets
                ws.delete_rows(idx, idx)

                # Send notification to all members
                members = []
                try:
                    members = json.loads(r.get("Members", "[]"))
                except: pass
                owner_name = r.get("OwnerName", "")
                address = r.get("Address", "")
                for m in members:
                    if m.get("userId") and m.get("userId") != user_id:
                        _create_notification_internal(
                            target_user_id=m["userId"],
                            notif_type="team_session_ended",
                            title="🔴 ทีมตรวจสิ้นสุด",
                            message=f"ทีมตรวจที่ {address or owner_name} ถูกปิดแล้ว",
                            link=""
                        )

                log_activity(user_id, "delete_team_session", f"Session {session_id}")
                return jsonify({"status": "ok"})

        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/team-sessions/all", methods=["GET"])
@require_auth
def list_all_team_sessions():
    """ดึง team sessions ทั้งหมด - สำหรับ admin เท่านั้น"""
    try:
        if request.user["role"] != "admin":
            return jsonify({"error": "Admin only"}), 403

        client = get_google_sheets_client()
        if not client:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        ws = get_or_create_worksheet(client, TEAM_SESSION_SHEET)
        if not ws:
            return jsonify({"error": "ระบบไม่พร้อมใช้งาน"}), 503

        records = safe_get_all_records(ws)
        sessions = []
        for r in records:
            if r.get("Status") == "active":
                members = []
                try:
                    members = json.loads(r.get("Members", "[]"))
                except: pass
                sessions.append({
                    "sessionId": r.get("SessionID"),
                    "ownerName": r.get("OwnerName"),
                    "address": r.get("Address"),
                    "members": members,
                    "lastUpdate": r.get("LastUpdate"),
                    "createdAt": r.get("CreatedAt")
                })

        return jsonify({"status": "ok", "sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== HELPERS =====

def save_local_backup(data):
    """สำรองข้อมูลลงไฟล์ local"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        filename = f"inspection_{data.get('id', 'unknown')}.json"
        filepath = os.path.join(backup_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Local backup error: {e}")


# ===== Vercel Entry Point =====
application = app
