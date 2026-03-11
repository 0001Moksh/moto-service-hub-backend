# Mechanic Portal Implementation Guide

## Overview
The Mechanic Portal has been successfully implemented with a complete invitation and signup flow, Aadhaar verification, and self-approval system.

## Architecture

### Data Persistence Pattern
```
Owner Invites Mechanic (Email + Name)
    ↓
Mechanic Receives Email with Invitation Link
    ↓
Step 1 (In Memory)    → Accept invitation, retrieve details
Step 2 (DATABASE INSERT) → Password setup creates mechanic record in DB (status="pending")
Step 3a (In Memory)    → Aadhaar upload and data extraction via Groq
Step 3b (DATABASE UPDATE) → Aadhaar verification updates mechanic record with status="active"
    ↓
Mechanic Signin → Email + password authentication
              → Access to mechanic dashboard
```

## API Endpoints

### Owner: Invite Mechanic

#### Invite Mechanic
```
POST /api/owner/invite-mechanic
Authorization: Bearer <owner_token>
Content-Type: application/json

Request:
{
  "mechanic_email": "mechanic@example.com",
  "mechanic_name": "Raj Kumar"
}

Query Parameters:
owner_id (required)

Response (200):
{
  "success": true,
  "message": "Mechanic invitation sent successfully",
  "invitation_token": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Mechanic Signup (Invitation-Based)

#### Step 1: Accept Invitation
```
POST /api/mechanic/signup/step1
Content-Type: application/json

Request:
{
  "invitation_token": "550e8400-e29b-41d4-a716-446655440000"
}

Response (200):
{
  "success": true,
  "message": "Invitation accepted. Now set your password.",
  "mechanic_email": "mechanic@example.com",
  "mechanic_name": "Raj Kumar"
}
```

#### Step 2: Set Password (Mechanic Created)
```
POST /api/mechanic/signup/step2
Content-Type: application/json

Request:
{
  "invitation_token": "550e8400-e29b-41d4-a716-446655440000",
  "password": "SecurePassword123"
}

Response (200):
{
  "success": true,
  "message": "Password set successfully. Now upload your Aadhaar card.",
  "mechanic_email": "mechanic@example.com"
}

Database Operation: INSERT into mechanic table with email, hashed password, status="pending"
```

#### Step 3a: Upload Aadhaar
```
POST /api/mechanic/signup/step3-upload-aadhaar
Content-Type: multipart/form-data

Parameters:
- invitation_token: "550e8400-e29b-41d4-a716-446655440000"
- file: <aadhaar_image.jpg>

Response (200):
{
  "success": true,
  "message": "Aadhaar data extracted successfully. Please verify the information.",
  "mechanic_email": "mechanic@example.com",
  "extracted_data": {
    "name": "Raj Kumar",
    "gender": "M",
    "dob": "1995-05-20",
    "aadhaar_number": "1234-5678-9012"
  }
}

Groq Processing:
- Image converted to base64
- Groq API extracts Aadhaar card text
- Returns: name, gender, DOB, aadhaar_number
```

#### Step 3b: Verify Aadhaar (Auto-Approval)
```
POST /api/mechanic/signup/step3-verify-aadhaar
Content-Type: application/json

Request:
{
  "invitation_token": "550e8400-e29b-41d4-a716-446655440000",
  "mechanic_name": "Raj Kumar",
  "gender": "M",
  "dob": "1995-05-20",
  "aadhaar_number": "1234-5678-9012"
}

Response (200):
{
  "success": true,
  "message": "Aadhaar verified! Your account is now active. You can now sign in.",
  "mechanic_email": "mechanic@example.com",
  "mechanic_id": 3
}

Database Operation: UPDATE mechanic table with aadhaar_number, name, gender, dob, status="active"
Invitation token is then deleted
```

### Mechanic Authentication

#### Mechanic Signin
```
POST /api/mechanic/signin
Content-Type: application/json

Request:
{
  "email": "mechanic@example.com",
  "password": "SecurePassword123"
}

Response (200):
{
  "success": true,
  "message": "Signin successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "mechanic": {
    "mechanic_id": 3,
    "shop_id": 1,
    "mechanic_email": "mechanic@example.com",
    "mechanic_name": "Raj Kumar",
    "gender": "M",
    "dob": "1995-05-20",
    "aadhaar_number": "1234-5678-9012",
    "status": "active"
  }
}
```

### Mechanic Profile

#### Get Mechanic Profile
```
GET /api/mechanic/profile/{mechanic_id}

Response (200):
{
  "success": true,
  "mechanic": {
    "mechanic_id": 3,
    "shop_id": 1,
    "mechanic_email": "mechanic@example.com",
    "mechanic_name": "Raj Kumar",
    "gender": "M",
    "dob": "1995-05-20",
    "aadhaar_number": "1234-5678-9012",
    "status": "active"
  }
}
```

### Owner: Manage Mechanics

#### List Shop Mechanics
```
GET /api/mechanic/shop/{owner_id}/mechanics
Authorization: Bearer <owner_token>

Response (200):
{
  "success": true,
  "total": 2,
  "mechanics": [
    {
      "mechanic_id": 1,
      "shop_id": 1,
      "mechanic_email": "mechanic1@example.com",
      "mechanic_name": "Worker One",
      "gender": "M",
      "dob": "1990-01-15",
      "aadhaar_number": "1111-2222-3333",
      "status": "active"
    },
    ...
  ]
}
```

#### Remove Mechanic
```
DELETE /api/mechanic/remove
Authorization: Bearer <owner_token>
Content-Type: application/json

Query Parameters:
owner_id (required)

Request:
{
  "mechanic_id": 1
}

Response (200):
{
  "success": true,
  "message": "Mechanic removed successfully"
}
```

## Database Tables Used

### mechanic (Created at Step 2)
```
- mechanic_id (PRIMARY KEY, AUTO INCREMENT)
- shop_id (FOREIGN KEY → shop)
- mechanic_email (UNIQUE)
- mechanic_name
- gender (NULLABLE, updated in Step 3)
- dob (NULLABLE, updated in Step 3)
- aadhaar_number (NULLABLE, updated in Step 3)
- password (NOT NULL, hashed)
- status ("pending" at Step 2 → "active" at Step 3)
- aadhaar_image_path (NULLABLE)
- created_at
- updated_at
```

## Error Handling

### Common Error Responses

**400 Bad Request - Invalid/Expired Token**
```json
{
  "detail": "Invalid or expired invitation token"
}
```

**400 Bad Request - Weak Password**
```json
{
  "detail": "Password must be at least 8 characters"
}
```

**400 Bad Request - Mechanic Already Exists**
```json
{
  "detail": "Mechanic already exists in this shop"
}
```

**400 Bad Request - Not Yet Active**
```json
{
  "detail": "Account not yet activated. Please complete Aadhaar verification."
}
```

**401 Unauthorized - Invalid Credentials**
```json
{
  "detail": "Invalid email or password"
}
```

**403 Forbidden - Not Authorized**
```json
{
  "detail": "Not authorized to remove this mechanic"
}
```

**404 Not Found**
```json
{
  "detail": "Mechanic not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error description"
}
```

## Testing Workflow

### Complete Mechanic Invitation & Signup Flow

1. **Owner Invites Mechanic:**
   ```
   POST /api/owner/invite-mechanic?owner_id=1
   {
     "mechanic_email": "raj@example.com",
     "mechanic_name": "Raj Kumar"
   }
   ```
   - Receive `invitation_token`
   - Email sent to mechanic

2. **Mechanic Accepts Invitation:**
   ```
   POST /api/mechanic/signup/step1
   { "invitation_token": "..." }
   ```

3. **Mechanic Sets Password:**
   ```
   POST /api/mechanic/signup/step2
   {
     "invitation_token": "...",
     "password": "MySecurePassword123"
   }
   ```

4. **Mechanic Uploads Aadhaar:**
   ```
   POST /api/mechanic/signup/step3-upload-aadhaar
   (multipart: invitation_token + aadhaar_image)
   ```
   - Verify extracted data (name, gender, DOB, Aadhaar number)

5. **Mechanic Verifies Aadhaar:**
   ```
   POST /api/mechanic/signup/step3-verify-aadhaar
   {
     "invitation_token": "...",
     "mechanic_name": "Raj Kumar",
     "gender": "M",
     "dob": "1995-05-20",
     "aadhaar_number": "1234-5678-9012"
   }
   ```
   - Account automatically activated

6. **Mechanic Signin:**
   ```
   POST /api/mechanic/signin
   {
     "email": "raj@example.com",
     "password": "MySecurePassword123"
   }
   ```
   - Receive JWT token

7. **Owner Lists Mechanics:**
   ```
   GET /api/mechanic/shop/1/mechanics
   ```

## File Uploads

### Aadhaar Image Upload
- **Location:** uploads/aadhaar/mechanic/{email}/
- **Supported Formats:** PNG, JPG, JPEG, GIF
- **Max Size:** 10MB
- **Processing:**
  - File saved with unique filename (UUID + timestamp)
  - Groq API extracts text from image
  - Path stored in mechanic record

## Security Features

1. **Invitation Tokens:** UUID-based, stored in-memory, 7-day expiry
2. **Password Hashing:** Bcrypt with salted hashing
3. **JWT Tokens:** HS256 with 30-minute expiry
4. **Email Verification:** Invitation emails sent via SMTP
5. **Aadhaar Security:**
   - Images stored securely
   - Aadhaar numbers stored separately
   - Unique constraint on aadhaar_number
6. **Database Constraints:**
   - Unique email and Aadhaar numbers
   - NOT NULL password requirement
   - Foreign key relationships

## Configuration Required

No additional configuration needed beyond the existing .env.local setup.

## Code Files

### Created/Modified Files
- `app/routers/mechanic.py` - Mechanic signup and management (413 lines)
- `app/routers/owner.py` - Added mechanic invite endpoint (+73 lines)
- `app/schemas/mechanic.py` - Pydantic models for mechanic flow (110 lines)
- `main.py` - Added mechanic router import and registration
- `test_mechanic_api.py` - Comprehensive test script

## Routes Summary

```
Owner Mechanics Management (Protected):
├── POST /api/owner/invite-mechanic          (Invite mechanic)
├── GET /api/mechanic/shop/{owner_id}/mechanics  (List mechanics)
└── DELETE /api/mechanic/remove               (Remove mechanic)

Mechanic Signup (Public, Invitation-based):
├── POST /api/mechanic/signup/step1           (Accept invitation)
├── POST /api/mechanic/signup/step2           (Set password)
├── POST /api/mechanic/signup/step3-upload-aadhaar  (Upload Aadhaar)
└── POST /api/mechanic/signup/step3-verify-aadhaar  (Verify Aadhaar)

Mechanic Authentication (Public):
└── POST /api/mechanic/signin                 (Login with JWT)

Mechanic Profile (Protected):
└── GET /api/mechanic/profile/{mechanic_id}   (Get profile)
```

## Key Features

✓ **Owner-Controlled Invitations:** Owners can only invite to their own shop
✓ **Email Notifications:** Mechanics receive invitation emails with login link
✓ **Progressive Signup:** 3-step process with automatic approval at Aadhaar verification
✓ **Automatic Status Activation:** No admin approval needed - activates at Aadhaar verification
✓ **Secure Storage:** Passwords hashed, Aadhaar isolated
✓ **Duplicate Prevention:** Unique email and Aadhaar constraints
✓ **JWT Authentication:** 30-minute session tokens
✓ **Groq Integration:** Automatic Aadhaar data extraction from images

## Differences from Owner Portal

1. **No OTP Required:** Uses invitation token instead of email OTP
2. **No Admin Approval:** Mechanics self-approve at Aadhaar verification
3. **Owner-Controlled:** Mechanics can only be invited by their shop owner
4. **Automatic Activation:** Status becomes "active" immediately after Aadhaar verification
5. **Shorter Flow:** Only 3 steps vs owner's 6 steps
6. **No Request Queue:** No pending requests table - direct activation

## Next Steps (Not Yet Implemented)

1. **Mechanic Dashboard:**
   - View assigned jobs
   - Update job status
   - Manage availability

2. **Mechanic Scheduling:**
   - Set working hours
   - Manage holidays
   - View calendar

3. **Job Assignment:**
   - Owner/dispatcher assigns jobs to mechanics
   - Mechanics accept/reject jobs

4. **Job Tracking:**
   - Real-time job status updates
   - Estimated completion times
   - Customer notifications
