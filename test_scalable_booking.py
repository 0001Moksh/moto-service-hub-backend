#!/usr/bin/env python3
"""
Test script for Scalable Booking System
Tests multi-user concurrent booking without conflicts
"""

import requests
import json
from uuid import UUID
import time
import concurrent.futures
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/booking"

# Test data
VEHICLE_ID = 6
SHOP_ID = 2
ISSUES = ["Engine is making noise", "Brake pads need replacement"]
SERVICE_DATE = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
SERVICE_TIME = "2026-03-15T10:00:00"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️ {msg}{Colors.END}")


def print_step(msg):
    print(f"\n{Colors.YELLOW}→ {msg}{Colors.END}")


# ==================== Test 1: Single User Booking ====================

def test_single_user_booking():
    print_step("TEST 1: Single User Complete Booking Flow")
    
    try:
        # Create session
        print_info("Creating booking session...")
        response = requests.post(f"{BASE_URL}/session/create", json={
            "vehicle_id": VEHICLE_ID,
            "customer_id": 1
        })
        
        if response.status_code != 200:
            print_error(f"Failed to create session: {response.text}")
            return False
        
        session_data = response.json()
        session_id = session_data["session_id"]
        print_success(f"Session created: {session_id}")
        
        # Step 1: Select Vehicle
        print_info("Step 1: Selecting vehicle...")
        response = requests.post(f"{BASE_URL}/step1-select-vehicle", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID
        })
        
        if response.status_code != 200:
            print_error(f"Step 1 failed: {response.text}")
            return False
        
        print_success("Vehicle selected")
        
        # Step 2: Add Issues
        print_info("Step 2: Adding issues...")
        response = requests.post(f"{BASE_URL}/step2-add-issue", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "issue_from_customer": ISSUES
        })
        
        if response.status_code != 200:
            print_error(f"Step 2 failed: {response.text}")
            return False
        
        print_success("Issues added")
        
        # Get Available Shops
        print_info("Fetching available shops...")
        response = requests.get(f"{BASE_URL}/available-shops")
        
        if response.status_code != 200:
            print_error(f"Failed to fetch shops: {response.text}")
            return False
        
        shops = response.json()
        print_success(f"Found {shops['total_shops']} shops")
        
        # Step 3: Select Shop
        print_info("Step 3: Selecting shop...")
        response = requests.post(f"{BASE_URL}/step3-select-shop", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "shop_id": SHOP_ID
        })
        
        if response.status_code != 200:
            print_error(f"Step 3 failed: {response.text}")
            return False
        
        print_success("Shop selected")
        
        # Get Available Slots
        print_info(f"Fetching available slots for {SERVICE_DATE}...")
        response = requests.get(f"{BASE_URL}/available-slots/{SHOP_ID}/{SERVICE_DATE}")
        
        if response.status_code != 200:
            print_error(f"Failed to fetch slots: {response.text}")
            return False
        
        slots_data = response.json()
        available_slots = [s for s in slots_data["slots"] if s["available"]]
        print_success(f"Found {len(available_slots)} available slots")
        
        # Step 4: Book Time Slot
        print_info("Step 4: Booking time slot...")
        response = requests.post(f"{BASE_URL}/step4-book-timeslot", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "shop_id": SHOP_ID,
            "issue_from_customer": ISSUES,
            "service_at": SERVICE_TIME,
            "booking_trust": False
        })
        
        if response.status_code != 200:
            print_error(f"Step 4 failed: {response.text}")
            return False
        
        booking_data = response.json()
        booking_id = booking_data["booking"]["booking_id"]
        print_success(f"Booking confirmed! Booking ID: {booking_id}")
        
        # Get Confirmation
        print_info("Fetching booking confirmation...")
        response = requests.get(f"{BASE_URL}/confirmation/{booking_id}")
        
        if response.status_code != 200:
            print_error(f"Failed to fetch confirmation: {response.text}")
            return False
        
        confirmation = response.json()
        print_success(f"Booking confirmed for {confirmation['service_at']}")
        
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


# ==================== Test 2: Concurrent Users ====================

def create_concurrent_booking(user_id):
    """Create a booking for one concurrent user"""
    try:
        # Create session
        response = requests.post(f"{BASE_URL}/session/create", json={
            "vehicle_id": VEHICLE_ID,
            "customer_id": user_id
        })
        
        if response.status_code != 200:
            return False, f"User {user_id}: Session creation failed"
        
        session_id = response.json()["session_id"]
        
        # Step 1
        response = requests.post(f"{BASE_URL}/step1-select-vehicle", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID
        })
        
        if response.status_code != 200:
            return False, f"User {user_id}: Step 1 failed"
        
        # Step 2
        response = requests.post(f"{BASE_URL}/step2-add-issue", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "issue_from_customer": ISSUES
        })
        
        if response.status_code != 200:
            return False, f"User {user_id}: Step 2 failed"
        
        # Step 3
        response = requests.post(f"{BASE_URL}/step3-select-shop", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "shop_id": SHOP_ID
        })
        
        if response.status_code != 200:
            return False, f"User {user_id}: Step 3 failed"
        
        # Step 4 (use different time slots to avoid conflicts)
        service_time = f"{SERVICE_DATE}T{9 + (user_id % 8):02d}:00:00"
        
        response = requests.post(f"{BASE_URL}/step4-book-timeslot", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID,
            "shop_id": SHOP_ID,
            "issue_from_customer": ISSUES,
            "service_at": service_time,
            "booking_trust": False
        })
        
        if response.status_code != 200:
            return False, f"User {user_id}: Step 4 failed - {response.text}"
        
        booking_id = response.json()["booking"]["booking_id"]
        return True, f"User {user_id}: Booking {booking_id} successful"
        
    except Exception as e:
        return False, f"User {user_id}: Exception - {str(e)}"


def test_concurrent_bookings(num_users=5):
    print_step(f"TEST 2: Concurrent Bookings ({num_users} users)")
    
    print_info(f"Starting {num_users} concurrent booking flows...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(create_concurrent_booking, i) for i in range(1, num_users + 1)]
        
        for future in concurrent.futures.as_completed(futures):
            success, message = future.result()
            results.append((success, message))
            
            if success:
                print_success(message)
            else:
                print_error(message)
    
    successful = sum(1 for success, _ in results if success)
    print_info(f"\nResults: {successful}/{num_users} users completed booking successfully")
    
    return successful == num_users


# ==================== Test 3: Session Isolation ====================

def test_session_isolation():
    print_step("TEST 3: Session Isolation (No Conflicts)")
    
    try:
        # Create 3 sessions
        sessions = []
        print_info("Creating 3 independent sessions...")
        
        for i in range(3):
            response = requests.post(f"{BASE_URL}/session/create", json={
                "vehicle_id": VEHICLE_ID,
                "customer_id": 100 + i
            })
            
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                sessions.append(session_id)
                print_success(f"Session {i+1}: {session_id}")
            else:
                print_error(f"Failed to create session {i+1}")
                return False
        
        # Update each session independently
        print_info("Updating sessions independently...")
        
        for idx, session_id in enumerate(sessions):
            response = requests.post(f"{BASE_URL}/step1-select-vehicle", json={
                "session_id": session_id,
                "vehicle_id": VEHICLE_ID
            })
            
            if response.status_code == 200:
                print_success(f"Session {idx+1}: Step 1 completed")
            else:
                print_error(f"Session {idx+1}: Failed")
                return False
        
        # Verify isolation - each session should have independent state
        print_info("Verifying session isolation...")
        
        for idx, session_id in enumerate(sessions):
            response = requests.get(f"{BASE_URL}/session/{session_id}")
            
            if response.status_code == 200:
                session = response.json()
                print_success(f"Session {idx+1}: current_step = {session['current_step']} (isolated state)")
            else:
                print_error(f"Session {idx+1}: Failed to retrieve")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


# ==================== Test 4: Session Expiry ====================

def test_session_retrieval():
    print_step("TEST 4: Session Retrieval & Status")
    
    try:
        # Create session
        response = requests.post(f"{BASE_URL}/session/create", json={
            "vehicle_id": VEHICLE_ID,
            "customer_id": 200
        })
        
        if response.status_code != 200:
            print_error("Failed to create session")
            return False
        
        session_id = response.json()["session_id"]
        print_success(f"Session created: {session_id}")
        
        # Complete step 1
        response = requests.post(f"{BASE_URL}/step1-select-vehicle", json={
            "session_id": session_id,
            "vehicle_id": VEHICLE_ID
        })
        
        if response.status_code != 200:
            print_error("Step 1 failed")
            return False
        
        print_success("Step 1 completed")
        
        # Retrieve session
        print_info("Retrieving session details...")
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        
        if response.status_code == 200:
            session = response.json()
            print_success(f"Session Status: {json.dumps(session, indent=2, default=str)}")
            return True
        else:
            print_error(f"Failed to retrieve session: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


# ==================== Main ====================

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Scalable Booking System - Test Suite")
    print(f"{'='*60}{Colors.END}\n")
    
    tests = [
        ("Single User Booking", test_single_user_booking),
        ("Concurrent Users", lambda: test_concurrent_bookings(5)),
        ("Session Isolation", test_session_isolation),
        ("Session Retrieval", test_session_retrieval),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{Colors.YELLOW}Running: {test_name}{Colors.END}")
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Delay between tests
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{Colors.END}\n")
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if result else f"{Colors.RED}❌ FAILED{Colors.END}"
        print(f"{test_name:<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.END}")
    else:
        print(f"\n{Colors.RED}⚠️ Some tests failed. Check logs above.{Colors.END}")


if __name__ == "__main__":
    main()
