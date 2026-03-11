"""
Test script for Customer Booking API
Run this on a running server: uvicorn main:app --reload
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Test Vehicle ID
TEST_VEHICLE_ID = 1
TEST_SHOP_ID = 5  # Adjust based on available shops


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Status: {response.status_code}")
        print(response.text)


def test_booking_step1():
    """Test Step 1: Select Vehicle"""
    print_response("STEP 1: SELECT VEHICLE", requests.post(
        f"{BASE_URL}/api/booking/step1-select-vehicle",
        json={"vehicle_id": TEST_VEHICLE_ID}
    ))


def test_booking_step2():
    """Test Step 2: Add Issue Description"""
    print_response("STEP 2: ADD ISSUE DESCRIPTIONS", requests.post(
        f"{BASE_URL}/api/booking/step2-add-issue",
        json={
            "vehicle_id": TEST_VEHICLE_ID,
            "issue_from_customer": [
                "Engine is making unusual grinding noise when starting",
                "Brake pedal feels soft"
            ]
        }
    ))


def test_get_available_shops():
    """Get all available shops"""
    print_response("GET AVAILABLE SHOPS", requests.get(
        f"{BASE_URL}/api/booking/available-shops"
    ))


def test_booking_step3(shop_id=TEST_SHOP_ID):
    """Test Step 3: Select Shop"""
    print_response("STEP 3: SELECT SHOP", requests.post(
        f"{BASE_URL}/api/booking/step3-select-shop",
        json={
            "vehicle_id": TEST_VEHICLE_ID,
            "shop_id": shop_id
        }
    ))


def test_get_available_slots(shop_id=TEST_SHOP_ID):
    """Get available time slots"""
    # Use tomorrow's date
    booking_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print_response(f"GET AVAILABLE SLOTS FOR {booking_date}", requests.get(
        f"{BASE_URL}/api/booking/available-slots/{shop_id}/{booking_date}"
    ))
    
    return booking_date


def test_booking_step4(shop_id=TEST_SHOP_ID):
    """Test Step 4: Book Time Slot"""
    # Use tomorrow at 11:00 AM
    tomorrow = datetime.now() + timedelta(days=1)
    service_at = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    
    print_response("STEP 4: BOOK TIME SLOT", requests.post(
        f"{BASE_URL}/api/booking/step4-book-timeslot",
        json={
            "vehicle_id": TEST_VEHICLE_ID,
            "shop_id": shop_id,
            "issue_from_customer": [
                "Engine is making unusual grinding noise when starting",
                "Brake pedal feels soft"
            ],
            "service_at": service_at,
            "booking_trust": False
        }
    ))
    
    return service_at


def test_get_booking_confirmation(booking_id=1):
    """Get booking confirmation"""
    print_response(f"GET BOOKING CONFIRMATION (ID: {booking_id})", requests.get(
        f"{BASE_URL}/api/booking/confirmation/{booking_id}"
    ))


def test_get_vehicle_bookings(vehicle_id=TEST_VEHICLE_ID):
    """Get all vehicle bookings"""
    print_response(f"GET VEHICLE BOOKINGS (ID: {vehicle_id})", requests.get(
        f"{BASE_URL}/api/booking/vehicle/{vehicle_id}"
    ))


def test_cancel_booking(booking_id=1):
    """Cancel a booking"""
    print_response(f"CANCEL BOOKING (ID: {booking_id})", requests.delete(
        f"{BASE_URL}/api/booking/cancel/{booking_id}"
    ))


def run_complete_booking_flow():
    """Run complete booking flow test"""
    print("\n" + "="*60)
    print("  COMPLETE BOOKING FLOW TEST")
    print("="*60)
    
    # Step 1: Select Vehicle
    test_booking_step1()
    input("\nPress Enter to continue to Step 2...")
    
    # Step 2: Add Issue
    test_booking_step2()
    input("\nPress Enter to continue to Step 3...")
    
    # Get available shops
    test_get_available_shops()
    
    # Step 3: Select Shop
    test_booking_step3()
    input("\nPress Enter to continue to get available slots...")
    
    # Get available slots
    booking_date = test_get_available_slots()
    input(f"\nPress Enter to book a slot for {booking_date}...")
    
    # Step 4: Book Time Slot
    test_booking_step4()
    input("\nPress Enter to retrieve all vehicle bookings...")
    
    # Get vehicle bookings
    test_get_vehicle_bookings()


if __name__ == "__main__":
    # Run interactive menu
    print("\n" + "="*60)
    print("  MOTO SERVICE HUB - BOOKING API TEST")
    print("="*60)
    print("\nOptions:")
    print("1. Test complete booking flow (interactive)")
    print("2. Test Step 1: Select Vehicle")
    print("3. Test Step 2: Add Issue")
    print("4. Test Get Available Shops")
    print("5. Test Step 3: Select Shop")
    print("6. Test Get Available Slots")
    print("7. Test Step 4: Book Time Slot")
    print("8. Test Get Booking Confirmation")
    print("9. Test Get Vehicle Bookings")
    print("10. Test Cancel Booking")
    print("0. Exit")
    
    while True:
        choice = input("\nEnter your choice (0-10): ")
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            run_complete_booking_flow()
        elif choice == "2":
            test_booking_step1()
        elif choice == "3":
            test_booking_step2()
        elif choice == "4":
            test_get_available_shops()
        elif choice == "5":
            shop_id = input("Enter shop_id (default 5): ") or "5"
            test_booking_step3(int(shop_id))
        elif choice == "6":
            shop_id = input("Enter shop_id (default 5): ") or "5"
            test_get_available_slots(int(shop_id))
        elif choice == "7":
            shop_id = input("Enter shop_id (default 5): ") or "5"
            test_booking_step4(int(shop_id))
        elif choice == "8":
            booking_id = input("Enter booking_id (default 1): ") or "1"
            test_get_booking_confirmation(int(booking_id))
        elif choice == "9":
            vehicle_id = input("Enter vehicle_id (default 1): ") or "1"
            test_get_vehicle_bookings(int(vehicle_id))
        elif choice == "10":
            booking_id = input("Enter booking_id to cancel (default 1): ") or "1"
            test_cancel_booking(int(booking_id))
        else:
            print("Invalid choice. Please try again.")
