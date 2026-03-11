# 🚀 Quick Start Guide - Moto Service Hub Backend

## ⚡ 5-Minute Setup

### 1. Activate Virtual Environment
```bash
cd backend
.\venv\Scripts\activate
```

### 2. Run the Server
```bash
python main.py
```

You should see:
```
==================================================
🚀 Moto Service Hub API Starting...
Version: 1.0.0
Environment: Development
==================================================
✅ Database connected
Uvicorn running on http://0.0.0.0:8000
```

### 3. Access the API
- **API Docs:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/health

---

## 📋 Project Files Overview

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point |
| `app/core/config.py` | Configuration & settings |
| `app/core/database.py` | Supabase connection |
| `app/routers/customer.py` | Customer auth & profile |
| `app/routers/vehicle.py` | Vehicle management |
| `app/routers/admin.py` | Admin operations |
| `app/utils/groq_service.py` | Groq LLM integration |
| `app/utils/otp.py` | OTP system |
| `app/utils/email.py` | Email sending |
| `app/utils/auth.py` | JWT & hashing |
| `app/utils/file_handler.py` | File uploads |

---

## 🔑 Key Endpoints

### Customer Signup (6 Steps)
```bash
# Step 1: Send email
curl -X POST http://localhost:8000/api/customer/signup/step1 \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Step 2: Verify OTP
curl -X POST http://localhost:8000/api/customer/signup/step2 \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# Step 3: Set password
curl -X POST http://localhost:8000/api/customer/signup/step3 \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123"}'

# Step 4: Add phone
curl -X POST http://localhost:8000/api/customer/signup/step4 \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "phone_number": "9876543210"}'

# Step 5: Upload Aadhaar (with image)
curl -X POST http://localhost:8000/api/customer/signup/step5-upload-aadhaar \
  -F "email=test@example.com" \
  -F "file=@aadhaar.jpg"

# Step 6: Verify & complete signup
curl -X POST http://localhost:8000/api/customer/signup/step6-verify-aadhaar \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "John Doe",
    "gender": "Male",
    "dob": "01/01/1990",
    "aadhaar_number": "123456789012"
  }'
```

### Customer Login
```bash
curl -X POST http://localhost:8000/api/customer/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123"}'
```

### Add Vehicle (2 Steps)
```bash
# Step 1: Upload RC
curl -X POST "http://localhost:8000/api/vehicle/add/step1-upload-rc?customer_id=1" \
  -F "file=@rc.jpg"

# Step 2: Verify & save
curl -X POST http://localhost:8000/api/vehicle/add/step2-verify-rc \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "reg_number": "MH01AB1234",
    "owner_name": "John Doe",
    "fuel": "Petrol",
    "manufacturer": "Bajaj",
    "color": "Black",
    "body_type": "Bike",
    "chassis_no": "XYZ123",
    "engine_no": "ABC456",
    "model_no": "Pulsar 150"
  }'
```

### Admin Login
```bash
curl -X POST "http://localhost:8000/api/admin/login?admin_key=0987654321"
```

---

## 📧 Environment Variables Required

Add these to `.env.local`:

```plaintext
# Core Settings
JWT_SECRET_KEY=your-secret-key-here

# Supabase (Already in .env.local)
NEXT_PUBLIC_SUPABASE_URL=https://brnsimoaoxuhpxzrfpcg.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# Email (Already in .env.local)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply.moksh.project@gmail.com
SMTP_PASS=samx njiy ggnv qsud

# Groq (Already in .env.local)
GROQ_API_KEY=YOUR_API_KEY_HERE

# Admin (Already in .env.local)
ADMIN_KEY=0987654321
NEXT_PUBLIC_ADMIN_MAIL=nofackai@gmail.com
```

---

## 🧪 Testing with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Signup Step 1
response = requests.post(
    f"{BASE_URL}/api/customer/signup/step1",
    json={"email": "test@example.com"}
)
print(json.dumps(response.json(), indent=2))

# 2. Signin
response = requests.post(
    f"{BASE_URL}/api/customer/signin",
    json={
        "email": "test@example.com", 
        "password": "SecurePass123"
    }
)
data = response.json()
token = data["access_token"]
print(f"Token: {token}")

# 3. Get Profile
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    f"{BASE_URL}/api/customer/profile/1",
    headers=headers
)
print(json.dumps(response.json(), indent=2))

# 4. Add Vehicle
with open("rc.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/api/vehicle/add/step1-upload-rc?customer_id=1",
        files=files
    )
print(json.dumps(response.json(), indent=2))
```

---

## 🛠️ Development Commands

```bash
# Activate venv
.\venv\Scripts\activate

# Run tests
pytest

# Check logs
type logs/app.log

# Install new package
pip install package-name
pip freeze > requirements.txt

# Deactivate venv
deactivate
```

---

## 📊 API Structure

```
├── /api/customer/
│   ├── signup/step1          (Email enrollment)
│   ├── signup/step2          (OTP verification)
│   ├── signup/step3          (Password setup)
│   ├── signup/step4          (Phone number)
│   ├── signup/step5-upload-aadhaar   (Image upload)
│   ├── signup/step6-verify-aadhaar   (Final verification)
│   ├── signin                (Login)
│   └── profile/{customer_id} (Get profile)
│
├── /api/vehicle/
│   ├── add/step1-upload-rc          (RC upload)
│   ├── add/step2-verify-rc          (Save vehicle)
│   ├── create                       (Direct creation)
│   ├── get/{vehicle_id}             (Get details)
│   ├── list/{customer_id}           (List vehicles)
│   ├── update/{vehicle_id}          (Update)
│   └── delete/{vehicle_id}          (Delete)
│
├── /api/admin/
│   ├── login                 (Admin login)
│   ├── stats                 (Dashboard stats)
│   ├── customers             (List customers)
│   └── vehicles              (List vehicles)
│
└── /
    ├── health                (Health check)
    └── /api/docs             (Swagger UI)
```

---

## ✅ Features Included

✅ **Customer Management**
- Multi-step signup with OTP verification
- Email-based authentication
- Aadhaar card OCR with Groq
- Secure password hashing

✅ **Vehicle Management**
- RC document OCR with Groq
- CRUD operations
- Multi-vehicle support
- Automatic data extraction

✅ **Admin Panel**
- Admin authentication
- Dashboard statistics
- Customer management
- Vehicle management

✅ **File Handling**
- Secure uploads
- Image processing
- Groq LLM integration
- Automatic cleanup

✅ **Security**
- JWT tokens
- Bcrypt password hashing
- Email verification
- OTP validation

---

## 🐛 Troubleshooting

**ModuleNotFoundError?**
```bash
pip install -r requirements.txt
```

**CORS errors?**
- Already configured in `main.py` for all origins
- Change in production: `allow_origins=["https://yourdomain.com"]`

**Database connection failed?**
- Check `.env.local` has valid Supabase credentials
- Verify internet connection
- Check Supabase status page

**Email not sending?**
- Verify SMTP credentials in `.env.local`
- Check app password (if using Gmail)
- Enable "Less secure app access" (Gmail)

**Image extraction failing?**
- Verify GROQ_API_KEY is valid
- Check image quality & format
- Ensure image file is readable

---

## 📞 Support

For issues or questions, check:
1. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Full API reference
2. Swagger UI: http://localhost:8000/api/docs
3. Error logs: `logs/app.log`

---

**Happy Development! 🎉**
