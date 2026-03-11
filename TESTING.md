# Moto Service Hub - CRUD Testing Guide

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### 3. Access Swagger UI
Open `http://localhost:8000/docs` in your browser to test endpoints interactively.

---

## API Endpoints Overview

### Health Check
- **GET** `/test/health` - Check if API is running

### Admin CRUD Operations
- **POST** `/test/admin/create` - Create new admin
- **GET** `/test/admin/list` - Get all admins
- **GET** `/test/admin/{admin_id}` - Get specific admin
- **PUT** `/test/admin/{admin_id}` - Update admin
- **DELETE** `/test/admin/{admin_id}` - Delete admin

### Customer CRUD Operations
- **POST** `/test/customer/create` - Create new customer
- **GET** `/test/customer/list` - Get all customers
- **GET** `/test/customer/{customer_id}` - Get specific customer
- **PUT** `/test/customer/{customer_id}` - Update customer
- **DELETE** `/test/customer/{customer_id}` - Delete customer

### Vehicle CRUD Operations
- **POST** `/test/vehicle/create` - Create new vehicle
- **GET** `/test/vehicle/list` - Get all vehicles
- **GET** `/test/vehicle/{vehicle_id}` - Get specific vehicle
- **PUT** `/test/vehicle/{vehicle_id}` - Update vehicle
- **DELETE** `/test/vehicle/{vehicle_id}` - Delete vehicle

### Test Query on Any Table
- **GET** `/test/query/{table_name}` - Query any table (returns first 100 records)

---

## Testing Workflow

### Step 1: Test Health
```bash
curl http://localhost:8000/test/health
```

### Step 2: Create a Record
```bash
curl -X POST http://localhost:8000/test/admin/create \
  -H "Content-Type: application/json" \
  -d '{"mail": "test@example.com", "password": "test123"}'
```

### Step 3: List Records
```bash
curl http://localhost:8000/test/admin/list
```

### Step 4: Get Specific Record
```bash
curl http://localhost:8000/test/admin/1
```

### Step 5: Update Record
```bash
curl -X PUT http://localhost:8000/test/admin/1 \
  -H "Content-Type: application/json" \
  -d '{"password": "newpassword"}'
```

### Step 6: Delete Record
```bash
curl -X DELETE http://localhost:8000/test/admin/1
```

---

## Using Swagger UI (Recommended)

1. Start the app: `python app.py`
2. Open `http://localhost:8000/docs`
3. Click on any endpoint to expand it
4. Click "Try it out"
5. Fill in the parameters
6. Click "Execute" to test

---

## Test Examples using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Create Admin
admin_data = {"mail": "admin@test.com", "password": "secure123"}
response = requests.post(f"{BASE_URL}/test/admin/create", json=admin_data)
print(response.json())

# List all admins
response = requests.get(f"{BASE_URL}/test/admin/list")
print(response.json())

# Create Customer
customer_data = {
    "mail": "customer@test.com",
    "password": "cust123",
    "phone_number": "9876543210"
}
response = requests.post(f"{BASE_URL}/test/customer/create", json=customer_data)
print(response.json())

# Create Vehicle
vehicle_data = {
    "reg_number": "MH01AB1234",
    "owner_name": "John Doe",
    "fuel": "petrol",
    "manufacturer": "Hero"
}
response = requests.post(f"{BASE_URL}/test/vehicle/create", json=vehicle_data)
print(response.json())

# Update Vehicle
update_data = {"fuel": "diesel", "manufacturer": "Bajaj"}
response = requests.put(f"{BASE_URL}/test/vehicle/1", json=update_data)
print(response.json())

# Delete Vehicle
response = requests.delete(f"{BASE_URL}/test/vehicle/1")
print(response.json())
```

---

## Notes

- The app uses **Supabase Service Role Key** for database operations (full access)
- All credentials are loaded from `.env.local`
- Error handling returns meaningful error messages
- Logging is enabled for debugging
- The API is organized by tags in Swagger for easy navigation

---

## Troubleshooting

**Connection Error?**
- Ensure `.env.local` has valid `NEXT_PUBLIC_SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Check internet connection to Supabase

**Table Not Found?**
- Verify the table exists in Supabase
- Check table name spelling (case-sensitive)

**401 Unauthorized?**
- Supabase key might be expired or revoked
- Generate new keys in Supabase dashboard

---

Enjoy testing! 🚀
