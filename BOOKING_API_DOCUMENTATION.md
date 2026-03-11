# Customer Booking API Implementation

## Overview
Complete 4-step booking system for customers to book motorcycle service appointments.

## Booking Flow

```
Step 1: Select Vehicle
       ↓
Step 2: Add Issue Description(s)
       ↓
Step 3: Select Shop
       ↓
Step 4: Book Service Time (CONFIRMED)
```

---

## API Endpoints

### 1️⃣ **Step 1: Select Vehicle**

```http
POST /api/booking/step1-select-vehicle
Content-Type: application/json

{
  "vehicle_id": 1
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Vehicle selected successfully. Now describe the issues.",
  "vehicle_id": 1,
  "vehicle": {
    "vehicle_id": 1,
    "reg_number": "MH02AB1234",
    "manufacturer": "Hero MotoCorp",
    "model_no": "Splendor Plus",
    "color": "Black",
    "body_type": "Commuter"
  },
  "step": "issue_description_required"
}
```

**Errors:**
- 404: Vehicle not found

---

### 2️⃣ **Step 2: Add Issue Description(s)**

```http
POST /api/booking/step2-add-issue
Content-Type: application/json

{
  "vehicle_id": 1,
  "issue_from_customer": [
    "Engine is making unusual grinding noise when starting",
    "Brake pedal feels soft"
  ]
}
```

**Request Parameters:**
- `vehicle_id`: int (required)
- `issue_from_customer`: array[string] (required) - Array of issue descriptions, each min 5 characters

**Response (201):**
```json
{
  "success": true,
  "message": "Issues recorded. Now select a shop.",
  "vehicle_id": 1,
  "issue_from_customer": [
    "Engine is making unusual grinding noise when starting",
    "Brake pedal feels soft"
  ],
  "step": "shop_selection_required"
}
```

**Errors:**
- 400: Vehicle selection not completed yet
- 400: Issue description too short (min 5 chars)
- 400: No issues provided

---

### 3️⃣ **Get Available Shops**

```http
GET /api/booking/available-shops
```

**Response (200):**
```json
{
  "success": true,
  "total_shops": 3,
  "shops": [
    {
      "shop_id": 5,
      "shop_name": "Hero Service Center",
      "shop_location": "Bangalore, MG Road",
      "phone_number": "9876543210",
      "rating": 4.5
    },
    {
      "shop_id": 6,
      "shop_name": "Quick Bike Repair",
      "shop_location": "Bangalore, Indiranagar",
      "phone_number": "9876543211",
      "rating": 4.3
    }
  ]
}
```

---

### 3️⃣ **Step 3: Select Shop**

```http
POST /api/booking/step3-select-shop
Content-Type: application/json

{
  "vehicle_id": 1,
  "shop_id": 5
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Shop selected. Now choose a date and time for service.",
  "vehicle_id": 1,
  "shop": {
    "shop_id": 5,
    "shop_name": "Hero Service Center",
    "shop_location": "Bangalore, MG Road",
    "phone_number": "9876543210",
    "rating": 4.5
  },
  "step": "timeslot_selection_required"
}
```

**Errors:**
- 400: Issue description not added yet
- 404: Shop not found
- 400: Vehicle/data mismatch

---

### 📅 **Get Available Time Slots**

```http
GET /api/booking/available-slots/5/2025-03-15
```

**Path Parameters:**
- `shop_id`: int (required)
- `booking_date`: string (required) - Format: YYYY-MM-DD

**Response (200):**
```json
{
  "success": true,
  "shop_id": 5,
  "shop_name": "Hero Service Center",
  "date": "2025-03-15",
  "slots": [
    {
      "date": "2025-03-15",
      "start_time": "09:00",
      "end_time": "10:00",
      "available": true
    },
    {
      "date": "2025-03-15",
      "start_time": "10:00",
      "end_time": "11:00",
      "available": false
    },
    {
      "date": "2025-03-15",
      "start_time": "11:00",
      "end_time": "12:00",
      "available": true
    }
  ]
}
```

**Errors:**
- 400: Cannot book for past dates
- 404: Shop not found

---

### 4️⃣ **Step 4: Book Service Time (Confirm Booking)**

```http
POST /api/booking/step4-book-timeslot
Content-Type: application/json

{
  "vehicle_id": 1,
  "shop_id": 5,
  "issue_from_customer": [
    "Engine is making unusual grinding noise when starting",
    "Brake pedal feels soft"
  ],
  "service_at": "2025-03-15T11:00:00",
  "booking_trust": false
}
```

**Request Parameters:**
- `vehicle_id`: int (required)
- `shop_id`: int (required)
- `issue_from_customer`: array[string] (required) - Array of issues
- `service_at`: string (required) - ISO 8601 format: YYYY-MM-DDTHH:MM:SS
- `booking_trust`: boolean (optional) - Default: false

**Response (201):**
```json
{
  "success": true,
  "message": "✅ Booking confirmed successfully!",
  "booking": {
    "booking_id": 42,
    "vehicle_id": 1,
    "shop_id": 5,
    "mechanic_id": null,
    "issue_from_customer": [
      "Engine is making unusual grinding noise when starting",
      "Brake pedal feels soft"
    ],
    "booking_trust": false,
    "status": "confirmed",
    "created_at": "2025-03-11T10:30:00.000000",
    "service_at": "2025-03-15T11:00:00",
    "cancelled_description": null
  },
  "step": "booking_confirmed"
}
```

**Errors:**
- 400: Shop selection not completed
- 400: Time slot already booked
- 400: Invalid datetime format

---

## Additional Endpoints

### ✅ Get Booking Confirmation

```http
GET /api/booking/confirmation/42
```

**Response (200):**
```json
{
  "success": true,
  "message": "Booking confirmed",
  "booking_id": 42,
  "vehicle_id": 1,
  "shop_id": 5,
  "shop_name": "Hero Service Center",
  "vehicle_reg_number": "MH02AB1234",
  "service_at": "2025-03-15T11:00:00",
  "issue_from_customer": [
    "Engine is making unusual grinding noise when starting",
    "Brake pedal feels soft"
  ],
  "booking_trust": false,
  "status": "confirmed"
}
```

---

### 📋 Get All Vehicle Bookings

```http
GET /api/booking/vehicle/1
```

**Response (200):**
```json
{
  "success": true,
  "vehicle_id": 1,
  "total_bookings": 2,
  "bookings": [
    {
      "booking_id": 42,
      "vehicle_reg_number": "MH02AB1234",
      "shop_name": "Hero Service Center",
      "service_at": "2025-03-15T11:00:00",
      "status": "confirmed",
      "issue_count": 2
    },
    {
      "booking_id": 41,
      "vehicle_reg_number": "MH02AB1234",
      "shop_name": "Quick Bike Repair",
      "service_at": "2025-03-10T14:00:00",
      "status": "completed",
      "issue_count": 1
    }
  ]
}
```

---

### ❌ Cancel Booking

```http
DELETE /api/booking/cancel/42?cancelled_description=Medical+emergency
```

**Query Parameters:**
- `cancelled_description`: string (optional) - Reason for cancellation

**Response (200):**
```json
{
  "success": true,
  "message": "Booking cancelled successfully",
  "booking_id": 42
}
```

**Errors:**
- 404: Booking not found
- 400: Cannot cancel a completed or already cancelled booking

---

## Complete Client Flow Example

```javascript
// Step 1: Select Vehicle
const vehicle = await fetch('/api/booking/step1-select-vehicle', {
  method: 'POST',
  body: JSON.stringify({ vehicle_id: 1 })
});

// Step 2: Add Issues
const issue = await fetch('/api/booking/step2-add-issue', {
  method: 'POST',
  body: JSON.stringify({
    vehicle_id: 1,
    issue_from_customer: [
      'Engine is making unusual noise',
      'Brake pedal feels soft'
    ]
  })
});

// Step 3: Get Available Shops
const shops = await fetch('/api/booking/available-shops');

// Step 3: Select Shop
const shop = await fetch('/api/booking/step3-select-shop', {
  method: 'POST',
  body: JSON.stringify({
    vehicle_id: 1,
    shop_id: 5
  })
});

// Get Available Time Slots
const slots = await fetch('/api/booking/available-slots/5/2025-03-15');

// Step 4: Complete Booking
const booking = await fetch('/api/booking/step4-book-timeslot', {
  method: 'POST',
  body: JSON.stringify({
    vehicle_id: 1,
    shop_id: 5,
    issue_from_customer: [
      'Engine is making unusual noise',
      'Brake pedal feels soft'
    ],
    service_at: '2025-03-15T11:00:00',
    booking_trust: false
  })
});

// Confirm Booking
const confirmation = await fetch('/api/booking/confirmation/42');
```

---

## Database Table Schema

```
booking
├── booking_id (bigint) - Primary Key
├── created_at (timestamp)
├── vehicle_id (bigint) - Foreign Key to vehicle
├── shop_id (bigint) - Foreign Key to owner
├── mechanic_id (bigint) - Foreign Key to mechanic (nullable)
├── booking_trust (boolean)
├── issue_from_customer (text[]) - Array of issues
├── status (varchar) - confirmed | pending | completed | cancelled
├── cancelled_description (text)
└── service_at (timestamp) - When service is scheduled
```

---

## Notes

- **Vehicle-based Tracking**: Bookings are tracked by vehicle_id, not customer_id
- **In-Memory Storage**: Booking progress is stored per vehicle_id in memory (use Redis in production)
- **Time Slots**: Currently 9 AM to 5 PM with 1-hour slots
- **Availability Check**: System checks for existing bookings before confirming
- **Validation**: All inputs are validated
- **Error Handling**: Comprehensive error messages for each scenario
- **ISO 8601 Format**: All timestamps use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

---

## Testing

You can test the booking flow using the provided endpoints at `/api/docs` after starting the server.

```bash
uvicorn main:app --reload
# Navigate to http://localhost:8000/api/docs
```

Or use the test script:
```bash
python test_booking_api.py
```
