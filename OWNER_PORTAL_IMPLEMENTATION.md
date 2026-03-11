# Owner Portal Implementation Guide

## Overview
The Owner Portal has been successfully implemented with a complete 6-step signup flow, admin approval workflow, and owner authentication system.

## Architecture

### Data Persistence Pattern
```
Step 1-2 (In Memory)    → Email signup, OTP generation and verification
Step 3 (DATABASE INSERT) → Password setup creates owner record in DB
Step 4-5 (In Memory)     → Aadhaar upload and extraction, stores in memory
Step 5 (DATABASE UPDATE) → Aadhaar data verification updates owner table
Step 6 (DATABASE INSERT) → Shop details submitted to request_shop table
                           Status: "pending" (awaiting admin approval)

Admin Approval → Creates owner account (if not already created)
              → Creates shop record linked to owner
              → Updates request_shop status to "approved"
              → Sends approval email

Owner Signin   → Uses email + password for authentication
              → Returns JWT access token
```

## API Endpoints

### Owner Signup (Public Endpoints)

#### Step 1: Email Signup
```
POST /api/owner/signup/step1
Content-Type: application/json

Request:
{
  "email": "owner@example.com"
}

Response (200):
{
  "success": true,
  "message": "OTP sent to your email. Check your inbox.",
  "email": "owner@example.com"
}
```

#### Step 2: OTP Verification
```
POST /api/owner/signup/step2
Content-Type: application/json

Request:
{
  "email": "owner@example.com",
  "otp": "123456"
}

Response (200):
{
  "success": true,
  "message": "OTP verified successfully. Now set your password.",
  "email": "owner@example.com"
}
```

#### Step 3: Password Setup (Owner Created)
```
POST /api/owner/signup/step3
Content-Type: application/json

Request:
{
  "email": "owner@example.com",
  "password": "SecurePassword123"
}

Response (200):
{
  "success": true,
  "message": "Password set successfully. Now upload your Aadhaar card.",
  "email": "owner@example.com"
}

Database Operation: INSERT into owner table with email and hashed password
```

#### Step 4: Upload Aadhaar
```
POST /api/owner/signup/step4-upload-aadhaar
Content-Type: multipart/form-data

Parameters:
- email: "owner@example.com"
- file: <aadhaar_image.jpg>

Response (200):
{
  "success": true,
  "message": "Aadhaar data extracted successfully. Please verify the information.",
  "email": "owner@example.com",
  "extracted_data": {
    "name": "John Doe",
    "gender": "M",
    "dob": "1990-01-15",
    "aadhaar_number": "1234-5678-9012"
  }
}

Groq Processing: 
- Image converted to base64
- Groq API extracts Aadhaar card text
- Returns: name, gender, DOB, aadhaar_number
```

#### Step 5: Verify Aadhaar Data
```
POST /api/owner/signup/step5-verify-aadhaar
Content-Type: application/json

Request:
{
  "email": "owner@example.com",
  "owner_name": "John Doe",
  "gender": "M",
  "dob": "1990-01-15",
  "aadhaar_number": "1234-5678-9012"
}

Response (200):
{
  "success": true,
  "message": "Aadhaar data verified. Now enter your shop details.",
  "email": "owner@example.com"
}

Database Operation: UPDATE owner table with aadhaar_number, gender, dob, owner_name
```

#### Step 6: Shop Details & Submit Request
```
POST /api/owner/signup/step6-submit-request
Content-Type: application/json

Request:
{
  "email": "owner@example.com",
  "shop_name": "John's Motorcycle Repair",
  "shop_location": "123 Main St, City, State",
  "phone_number": "9876543210"
}

Response (200):
{
  "success": true,
  "message": "Shop request submitted successfully! Admin will review and send approval via email.",
  "request_id": 5,
  "status": "pending"
}

Database Operation: INSERT into request_shop table with status="pending"
```

### Owner Authentication (Public Endpoint)

#### Owner Signin
```
POST /api/owner/signin
Content-Type: application/json

Request:
{
  "email": "owner@example.com",
  "password": "SecurePassword123"
}

Response (200):
{
  "success": true,
  "message": "Signin successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "owner": {
    "owner_id": 1,
    "mail": "owner@example.com",
    "owner_name": "John Doe",
    "gender": "M",
    "dob": "1990-01-15",
    "aadhaar_number": "1234-5678-9012"
  }
}

Note: Owner must be approved first (admin must approve shop request)
```

### Owner Profile (Protected Endpoint)

#### Get Owner Profile
```
GET /api/owner/profile/{owner_id}
Authorization: Bearer <access_token>

Response (200):
{
  "success": true,
  "owner": {
    "owner_id": 1,
    "mail": "owner@example.com",
    "owner_name": "John Doe",
    "gender": "M",
    "dob": "1990-01-15",
    "aadhaar_number": "1234-5678-9012"
  }
}
```

## Admin Endpoints

### List Shop Requests
```
GET /api/admin/shop-requests
GET /api/admin/shop-requests?status=pending
GET /api/admin/shop-requests?status=approved
GET /api/admin/shop-requests?status=rejected
Authorization: Bearer <admin_token>

Response (200):
{
  "success": true,
  "total": 3,
  "requests": [
    {
      "request_id": 1,
      "mail": "owner1@example.com",
      "owner_name": "Owner One",
      "shop_name": "Shop One",
      "shop_location": "Location 1",
      "phone_number": "1234567890",
      "status": "pending"
    },
    ...
  ]
}
```

### Get Single Request
```
GET /api/admin/shop-requests/{request_id}
Authorization: Bearer <admin_token>

Response (200):
{
  "success": true,
  "request": {
    "request_id": 1,
    "mail": "owner@example.com",
    "owner_name": "John Doe",
    "gender": "M",
    "dob": "1990-01-15",
    "aadhaar_number": "1234-5678-9012",
    "shop_name": "John's Motorcycle Repair",
    "shop_location": "123 Main St, City, State",
    "phone_number": "9876543210",
    "status": "pending"
  }
}
```

### Approve Shop Request
```
POST /api/admin/approve-shop
Content-Type: application/json
Authorization: Bearer <admin_token>

Request:
{
  "request_id": 1
}

Response (200):
{
  "success": true,
  "message": "Shop request approved successfully. Owner account created and email sent.",
  "owner_id": 5,
  "request_id": 1
}

Database Operations:
1. INSERT into owner table (if not exists)
2. INSERT into shop table linked to owner_id
3. UPDATE request_shop status to "approved"
4. SEND email to owner with approval message
```

### Reject Shop Request
```
POST /api/admin/reject-shop
Content-Type: application/json
Authorization: Bearer <admin_token>

Request:
{
  "request_id": 1,
  "reason": "Documentation incomplete or invalid"
}

Response (200):
{
  "success": true,
  "message": "Shop request rejected. Email notification sent.",
  "request_id": 1
}

Database Operations:
1. UPDATE request_shop status to "rejected"
2. SEND email to owner with rejection message
```

## Database Tables Used

### request_shop (Pending Approval)
```
- request_id (PRIMARY KEY, AUTO INCREMENT)
- mail (owner email)
- owner_name
- gender
- dob
- aadhaar_number
- password (hashed)
- shop_name
- shop_location
- phone_number
- status (pending/approved/rejected)
- created_at (timestamp)
```

### owner (After Approval)
```
- owner_id (PRIMARY KEY, AUTO INCREMENT)
- mail (UNIQUE)
- owner_name
- gender
- dob
- aadhaar_number (UNIQUE)
- password (NOT NULL, hashed)
- created_at
- updated_at
```

### shop (After Approval)
```
- shop_id (PRIMARY KEY, AUTO INCREMENT)
- owner_id (FOREIGN KEY → owner)
- shop_name
- shop_location
- phone_number
- created_at
```

## Error Handling

### Common Error Responses

**400 Bad Request - Email Already Registered**
```json
{
  "detail": "Email already registered as owner"
}
```

**400 Bad Request - Invalid OTP**
```json
{
  "detail": "Invalid or expired OTP"
}
```

**400 Bad Request - Weak Password**
```json
{
  "detail": "Password must be at least 8 characters"
}
```

**400 Bad Request - File Upload Failed**
```json
{
  "detail": "Invalid file format or size exceeds limit"
}
```

**400 Bad Request - Invalid Credentials**
```json
{
  "detail": "Invalid email or password"
}
```

**404 Not Found - Owner Not Found**
```json
{
  "detail": "Owner not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error description"
}
```

## Testing Workflow

### Complete Owner Signup Flow
1. **Step 1:** POST /api/owner/signup/step1 with email
   - Check email for OTP
   
2. **Step 2:** POST /api/owner/signup/step2 with email and OTP (6-digit)
   
3. **Step 3:** POST /api/owner/signup/step3 with email and password (min 8 chars)
   
4. **Step 4:** POST /api/owner/signup/step4-upload-aadhaar with Aadhaar image
   - Verify extracted data (name, gender, DOB, Aadhaar number)
   
5. **Step 5:** POST /api/owner/signup/step5-verify-aadhaar with verified Aadhaar data
   
6. **Step 6:** POST /api/owner/signup/step6-submit-request with shop details
   - Receive request_id

### Admin Approval Flow
1. **Admin Login:** POST /api/admin/login with admin_key
   
2. **List Requests:** GET /api/admin/shop-requests?status=pending
   
3. **Review Request:** GET /api/admin/shop-requests/{request_id}
   
4. **Approve:** POST /api/admin/approve-shop with request_id
   - Check email for approval notification
   - Owner account is created automatically
   
5. **Owner Signin:** POST /api/owner/signin with email and password
   - Receive JWT token
   
6. **Get Profile:** GET /api/owner/profile/{owner_id} with Bearer token

## File Uploads

### Aadhaar Image Upload
- **Location:** uploads/aadhaar/owner/{email}/
- **Supported Formats:** PNG, JPG, JPEG, GIF
- **Max Size:** 10MB
- **Processing:** 
  - File saved with unique filename (UUID + timestamp)
  - Groq API extracts text from image
  - Path stored in owner record

## Security Features

1. **Password Hashing:** Bcrypt with salted hashing
2. **JWT Tokens:** HS256 with 30-minute expiry
3. **OTP Validation:** 6-digit codes with 10-minute expiry, max 5 attempts
4. **Email Verification:** SMTP-based OTP delivery
5. **Aadhaar Security:** 
   - Images stored securely
   - Aadhaar numbers stored separately
   - Unique constraint on aadhaar_number
6. **Database Constraints:**
   - Unique email and phone numbers
   - NOT NULL password requirement
   - Foreign key relationships

## Configuration Required

Add to `.env.local`:
```
FRONTEND_URL=http://localhost:3000  # For signup completion emails
```

## Next Steps (Not Yet Implemented)

1. **Mechanic/Worker Signup:**
   - Owner invites mechanic
   - Personalized login link via email
   - Mechanic self-approval after Aadhaar verification
   
2. **Owner Dashboard:**
   - View shop details
   - Add mechanics
   - Manage workers
   - View bookings
   
3. **Mechanic Dashboard:**
   - View assigned jobs
   - Update job status
   - View availability

## Code Files

### Created/Modified Files
- `app/routers/owner.py` - Owner signup and authentication (287 lines)
- `app/routers/admin.py` - Shop request management (added ~200 lines)
- `app/schemas/owner.py` - Pydantic models for owner flow (already created)
- `main.py` - Added owner router import and registration
- `app/core/config.py` - Added FRONTEND_URL setting

### Imports Used
- fastapi, pydantic, supabase, groq
- app.utils: otp, email, auth, file_handler, groq_service
- app.core: config, database
- app.schemas: owner

## Routes Summary

```
Owner Signup (Public):
├── POST /api/owner/signup/step1         (Email signup)
├── POST /api/owner/signup/step2         (OTP verification)
├── POST /api/owner/signup/step3         (Password setup)
├── POST /api/owner/signup/step4-upload-aadhaar   (Aadhaar upload)
├── POST /api/owner/signup/step5-verify-aadhaar   (Aadhaar verification)
└── POST /api/owner/signup/step6-submit-request   (Shop submission)

Owner Authentication (Public):
└── POST /api/owner/signin               (Login with JWT)

Owner Profile (Protected):
└── GET /api/owner/profile/{owner_id}    (Get profile)

Admin Management (Protected):
├── GET /api/admin/shop-requests         (List requests)
├── GET /api/admin/shop-requests/{id}    (Get request)
├── POST /api/admin/approve-shop         (Approve request)
└── POST /api/admin/reject-shop          (Reject request)
```
