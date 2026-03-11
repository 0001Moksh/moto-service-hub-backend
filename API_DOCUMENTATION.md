# Moto Service Hub - Backend API Documentation

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   └── database.py         # Supabase connection
│   ├── models/
│   │   └── __init__.py         # SQLAlchemy/Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── customer.py         # Customer auth & profile
│   │   ├── vehicle.py          # Vehicle management
│   │   └── admin.py            # Admin operations
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── customer.py         # Customer request/response schemas
│   │   └── vehicle.py          # Vehicle schemas
│   └── utils/
│       ├── __init__.py
│       ├── otp.py              # OTP generation & verification
│       ├── email.py            # Email sending
│       ├── auth.py             # JWT & password hashing
│       ├── file_handler.py     # File upload handling
│       └── groq_service.py     # Groq LLM integration
├── uploads/                     # Uploaded files
├── logs/                        # Application logs
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
├── .env.local                   # Environment variables
└── venv/                        # Virtual environment
```

---

## Setup Instructions

### 1. Create & Activate Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add JWT_SECRET_KEY to .env.local
```bash
JWT_SECRET_KEY="your-super-secret-key-change-in-production"
```

### 4. Run the Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## Customer Authentication Flow

### Step 1️⃣: Email Signup
```http
POST /api/customer/signup/step1
Content-Type: application/json

{
  "email": "customer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent to your email. Check your inbox.",
  "email": "customer@example.com",
  "step": "otp_sent"
}
```

### Step 2️⃣: Verify OTP
```http
POST /api/customer/signup/step2
Content-Type: application/json

{
  "email": "customer@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully. Now set your password.",
  "email": "customer@example.com",
  "step": "password_required"
}
```

### Step 3️⃣: Set Password
```http
POST /api/customer/signup/step3
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password set successfully. Now add your phone number.",
  "email": "customer@example.com",
  "step": "phone_required"
}
```

### Step 4️⃣: Add Phone Number
```http
POST /api/customer/signup/step4
Content-Type: application/json

{
  "email": "customer@example.com",
  "phone_number": "9876543210"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Phone number saved. Now upload your Aadhaar card for verification.",
  "email": "customer@example.com",
  "step": "aadhaar_upload_required"
}
```

### Step 5️⃣: Upload & Extract Aadhaar
```http
POST /api/customer/signup/step5-upload-aadhaar
Content-Type: multipart/form-data

email: customer@example.com
file: [aadhaar_image.jpg]
```

**Response:**
```json
{
  "success": true,
  "message": "Aadhaar data extracted successfully. Please verify the information.",
  "email": "customer@example.com",
  "extracted_data": {
    "name": "John Doe",
    "gender": "Male",
    "dob": "01/01/1990",
    "aadhaar_number": "123456789012"
  },
  "step": "verify_aadhaar_data"
}
```

### Step 6️⃣: Verify Aadhaar Data & Complete Signup
```http
POST /api/customer/signup/step6-verify-aadhaar
Content-Type: application/json

{
  "email": "customer@example.com",
  "name": "John Doe",
  "gender": "Male",
  "dob": "01/01/1990",
  "aadhaar_number": "123456789012"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Signup completed successfully! Welcome to Moto Service Hub.",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "customer": {
    "customer_id": 1,
    "mail": "customer@example.com",
    "phone_number": "9876543210",
    "name": "John Doe",
    "gender": "Male",
    "dob": "01/01/1990",
    "aadhaar_number": "123456789012"
  }
}
```

---

## Customer Login

```http
POST /api/customer/signin
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Signin successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "customer": {
    "customer_id": 1,
    "mail": "customer@example.com",
    "phone_number": "9876543210",
    "name": "John Doe",
    "gender": "Male",
    "dob": "01/01/1990",
    "aadhaar_number": "123456789012"
  }
}
```

---

## Vehicle Management Flow

### Step 1️⃣: Upload RC & Extract Data
```http
POST /api/vehicle/add/step1-upload-rc?customer_id=1
Content-Type: multipart/form-data

file: [rc_image.jpg]
```

**Response:**
```json
{
  "success": true,
  "message": "RC data extracted successfully. Please verify the information.",
  "extracted_data": {
    "reg_number": "MH01AB1234",
    "owner_name": "John Doe",
    "vehicle_class": "Light Motor Vehicle",
    "fuel_type": "Petrol",
    "manufacturer": "Bajaj",
    "model": "Pulsar 150",
    "chassis_number": "XYZ123",
    "engine_number": "ABC456",
    "registration_date": "01/01/2020",
    "color": "Black",
    "body_type": "Bike"
  },
  "step": "verify_rc_data"
}
```

### Step 2️⃣: Verify RC Data & Save Vehicle
```http
POST /api/vehicle/add/step2-verify-rc
Content-Type: application/json

{
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
}
```

**Response:**
```json
{
  "success": true,
  "message": "Vehicle added successfully!",
  "vehicle": {
    "vehicle_id": 1,
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
  }
}
```

---

## Vehicle CRUD Operations

### Get Vehicle
```http
GET /api/vehicle/get/{vehicle_id}
```

### List Customer Vehicles
```http
GET /api/vehicle/list/{customer_id}
```

### Update Vehicle
```http
PUT /api/vehicle/update/{vehicle_id}
Content-Type: application/json

{
  "fuel": "Diesel",
  "color": "White"
}
```

### Delete Vehicle
```http
DELETE /api/vehicle/delete/{vehicle_id}
```

---

## Admin Operations

### Admin Login
```http
POST /api/admin/login?admin_key=0987654321
```

**Response:**
```json
{
  "success": true,
  "message": "Admin login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "admin": {
    "admin_id": 1,
    "mail": "nofackai@gmail.com"
  }
}
```

### Get Dashboard Stats
```http
GET /api/admin/stats
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_customers": 10,
    "total_vehicles": 15,
    "total_bookings": 5,
    "total_services": 3
  }
}
```

### List All Customers
```http
GET /api/admin/customers?limit=100&offset=0
```

### List All Vehicles
```http
GET /api/admin/vehicles?limit=100&offset=0
```

---

## Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "app": "Moto Service Hub",
  "version": "1.0.0",
  "timestamp": "2026-03-10T10:30:00.000000",
  "database": {
    "status": "connected",
    "message": "Database connection successful"
  }
}
```

---

## Error Handling

All errors return the following format:

```json
{
  "success": false,
  "error": "Error message",
  "status_code": 400
}
```

Common status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

---

## Key Features Implemented

✅ **Customer Authentication**
- Email-based signup with OTP verification
- Secure password hashing with bcrypt
- JWT token-based authentication
- Customer profile management

✅ **Aadhaar Integration**
- Image upload & processing
- Groq LLM-based data extraction
- Manual verification & editing
- Secure storage

✅ **Vehicle Management**
- RC (Registration Certificate) upload
- Automatic data extraction using Groq
- CRUD operations
- Multi-vehicle support per customer

✅ **Admin Dashboard**
- Admin authentication
- Statistics & analytics
- Customer & vehicle management

✅ **File Handling**
- Secure file upload
- Unique filename generation
- File size validation
- Automatic cleanup

✅ **Email Notifications**
- OTP emails
- Welcome emails
- Async email sending

✅ **Logging & Monitoring**
- Comprehensive logging
- Error tracking
- Startup/shutdown events
- Request logging

---

## Technologies Used

- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
- **Authentication:** JWT with python-jose
- **Password Hashing:** Bcrypt
- **Image Processing:** Groq LLM API
- **Email:** SMTP
- **File Upload:** Multipart form data
- **Async:** Python asyncio
- **Server:** Uvicorn

---

## Environment Variables

```plaintext
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# JWT
JWT_SECRET_KEY=your-secret-key

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Groq LLM
GROQ_API_KEY=your-groq-api-key

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_KEY=your-admin-key
```

---

## Testing with Swagger UI

1. Open `http://localhost:8000/api/docs`
2. All endpoints are organized by tags (Customer, Vehicle, Admin)
3. Click "Try it out" to test any endpoint
4. Add Authorization header for protected routes:
   ```
   Authorization: Bearer <access_token>
   ```

---

## Future Enhancements

- [ ] Booking management system
- [ ] Job tracking for mechanics
- [ ] Service history
- [ ] Payment integration
- [ ] Push notifications
- [ ] Shop management features
- [ ] Rating & reviews system
- [ ] Real-time updates with WebSockets

---

**Created:** March 10, 2026  
**Version:** 1.0.0  
**Status:** ✅ Ready for Testing
