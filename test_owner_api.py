"""
Owner Portal API Testing Guide
Run this after starting the FastAPI server with: uvicorn main:app --reload
"""

import requests
import json
from typing import Dict, Any
import time

BASE_URL = "http://localhost:8000"
ADMIN_KEY = "your-admin-key"  # Replace with actual admin key

class OwnerAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_email = f"owner_test_{int(time.time())}@example.com"
        self.owner_data = {}
        
    def print_response(self, title: str, response: requests.Response, expect_200: bool = True):
        """Pretty print API response"""
        status = "PASS" if (response.status_code == 200 and expect_200) or (response.status_code != 200 and not expect_200) else "FAIL"
        print(f"\n[{status}] {title}")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
        return response.status_code < 300
    
    def test_step1_email_signup(self) -> bool:
        """Test Step 1: Email signup"""
        url = f"{self.base_url}/api/owner/signup/step1"
        payload = {"email": self.test_email}
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Step 1: Email Signup", response)
        
        if success and response.json().get("success"):
            self.owner_data["email"] = self.test_email
            print("✓ Email registered, OTP sent (check console/email)")
        return success
    
    def test_step2_otp_verification(self, otp: str = "123456") -> bool:
        """Test Step 2: OTP verification"""
        url = f"{self.base_url}/api/owner/signup/step2"
        payload = {
            "email": self.test_email,
            "otp": otp
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Step 2: OTP Verification", response)
        
        if success and response.json().get("success"):
            self.owner_data["otp_verified"] = True
        return success
    
    def test_step3_password_setup(self, password: str = "TestPassword123") -> bool:
        """Test Step 3: Password setup"""
        url = f"{self.base_url}/api/owner/signup/step3"
        payload = {
            "email": self.test_email,
            "password": password
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Step 3: Password Setup", response)
        
        if success and response.json().get("success"):
            self.owner_data["password"] = password
            self.owner_data["owner_created"] = True
        return success
    
    def test_step4_aadhaar_upload(self, image_path: str = None) -> bool:
        """Test Step 4: Aadhaar upload and extraction"""
        url = f"{self.base_url}/api/owner/signup/step4-upload-aadhaar"
        
        # Check if real image exists
        if image_path and __import__('os').path.exists(image_path):
            with open(image_path, 'rb') as f:
                files = {'file': f}
                data = {'email': self.test_email}
                response = self.session.post(url, data=data, files=files)
        else:
            # Use a dummy test without real image
            print("\n[INFO] Step 4: Aadhaar Upload - Skipped (no image provided)")
            print("To test, call with image_path parameter: test_step4_aadhaar_upload('path/to/aadhaar.jpg')")
            self.owner_data["aadhaar_extracted"] = {
                "name": "John Doe",
                "gender": "M",
                "dob": "1990-01-15",
                "aadhaar_number": "1234-5678-9012"
            }
            return True
        
        success = self.print_response("Step 4: Aadhaar Upload", response)
        
        if success and response.json().get("success"):
            self.owner_data["aadhaar_extracted"] = response.json().get("extracted_data", {})
        return success
    
    def test_step5_verify_aadhaar(self) -> bool:
        """Test Step 5: Verify Aadhaar data"""
        url = f"{self.base_url}/api/owner/signup/step5-verify-aadhaar"
        
        # Use extracted data from step 4
        aadhaar_data = self.owner_data.get("aadhaar_extracted", {
            "name": "John Doe",
            "gender": "M",
            "dob": "1990-01-15",
            "aadhaar_number": "1234-5678-9012"
        })
        
        payload = {
            "email": self.test_email,
            "owner_name": aadhaar_data.get("name", "John Doe"),
            "gender": aadhaar_data.get("gender", "M"),
            "dob": aadhaar_data.get("dob", "1990-01-15"),
            "aadhaar_number": aadhaar_data.get("aadhaar_number", "1234-5678-9012")
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Step 5: Verify Aadhaar Data", response)
        
        if success and response.json().get("success"):
            self.owner_data["aadhaar_verified"] = True
        return success
    
    def test_step6_submit_request(self) -> bool:
        """Test Step 6: Submit shop request"""
        url = f"{self.base_url}/api/owner/signup/step6-submit-request"
        
        payload = {
            "email": self.test_email,
            "shop_name": "Test Motorcycle Repair Shop",
            "shop_location": "123 Main Street, Test City, TS 12345",
            "phone_number": "9876543210"
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Step 6: Submit Shop Request", response)
        
        if success and response.json().get("success"):
            self.owner_data["request_id"] = response.json().get("request_id")
            self.owner_data["request_submitted"] = True
        return success
    
    def test_owner_signin(self) -> bool:
        """Test owner signin"""
        url = f"{self.base_url}/api/owner/signin"
        
        payload = {
            "email": self.test_email,
            "password": self.owner_data.get("password", "TestPassword123")
        }
        
        response = self.session.post(url, json=payload)
        # Might fail before approval, so not testing for 200
        self.print_response("Owner Signin (may fail before approval)", response, expect_200=False)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.owner_data["access_token"] = token
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return True
        return False
    
    def test_owner_profile(self, owner_id: int = 1) -> bool:
        """Test get owner profile"""
        url = f"{self.base_url}/api/owner/profile/{owner_id}"
        
        response = self.session.get(url)
        self.print_response(f"Get Owner Profile (owner_id={owner_id})", response, expect_200=False)
        return response.status_code < 300
    
    def test_admin_login(self, admin_key: str = ADMIN_KEY) -> bool:
        """Test admin login"""
        url = f"{self.base_url}/api/admin/login"
        
        payload = {"admin_key": admin_key}
        response = self.session.post(url, json=payload)
        success = self.print_response("Admin Login", response)
        
        if success and response.json().get("success"):
            token = response.json().get("access_token")
            self.owner_data["admin_token"] = token
            return True
        return False
    
    def test_list_shop_requests(self, status: str = None) -> bool:
        """Test list shop requests"""
        url = f"{self.base_url}/api/admin/shop-requests"
        if status:
            url += f"?status={status}"
        
        headers = {"Authorization": f"Bearer {self.owner_data.get('admin_token', '')}"}
        response = self.session.get(url, headers=headers)
        
        self.print_response(f"Admin: List Shop Requests (status={status})", response)
        return response.status_code < 300
    
    def test_get_shop_request(self, request_id: int) -> bool:
        """Test get single shop request"""
        url = f"{self.base_url}/api/admin/shop-requests/{request_id}"
        
        headers = {"Authorization": f"Bearer {self.owner_data.get('admin_token', '')}"}
        response = self.session.get(url, headers=headers)
        
        self.print_response(f"Admin: Get Shop Request (id={request_id})", response)
        return response.status_code < 300
    
    def test_approve_shop(self, request_id: int) -> bool:
        """Test approve shop request"""
        url = f"{self.base_url}/api/admin/approve-shop"
        
        payload = {"request_id": request_id}
        headers = {"Authorization": f"Bearer {self.owner_data.get('admin_token', '')}"}
        response = self.session.post(url, json=payload, headers=headers)
        
        success = self.print_response("Admin: Approve Shop Request", response)
        
        if success and response.json().get("success"):
            self.owner_data["owner_id"] = response.json().get("owner_id")
        return success
    
    def test_reject_shop(self, request_id: int, reason: str = "Documentation incomplete") -> bool:
        """Test reject shop request"""
        url = f"{self.base_url}/api/admin/reject-shop"
        
        params = {"request_id": request_id, "reason": reason}
        headers = {"Authorization": f"Bearer {self.owner_data.get('admin_token', '')}"}
        response = self.session.post(url, params=params, headers=headers)
        
        self.print_response("Admin: Reject Shop Request", response)
        return response.status_code < 300
    
    def run_complete_flow_test(self):
        """Run complete owner signup flow"""
        print("\n" + "="*60)
        print("OWNER PORTAL - COMPLETE FLOW TEST")
        print("="*60)
        
        print(f"\nTest Email: {self.test_email}")
        print("Note: OTP verification will fail with dummy OTP. Use real OTP from email.")
        
        # Owner Signup Flow
        print("\n--- OWNER SIGNUP FLOW ---")
        if not self.test_step1_email_signup():
            print("Failed at Step 1")
            return
        
        # Manually enter OTP or skip for automated testing
        print("\n[MANUAL ACTION REQUIRED] Check your email for the OTP and run:")
        print(f"tester.test_step2_otp_verification('YOUR_OTP_HERE')")
        
        # For automated testing, simulate going through the steps (OTP will fail in real test)
        print("\n[INFO] Simulating OTP verification (will fail in real test without valid OTP)")
        
        # Try with dummy OTP - this will fail but shows the full flow
        if self.test_step2_otp_verification("000000"):
            if self.test_step3_password_setup():
                self.test_step4_aadhaar_upload()
                self.test_step5_verify_aadhaar()
                self.test_step6_submit_request()
        
        # Admin Flow
        print("\n--- ADMIN APPROVAL FLOW ---")
        if self.test_admin_login():
            self.test_list_shop_requests("pending")
            
            # If we have a request_id from our submission, test approval
            if self.owner_data.get("request_id"):
                self.test_get_shop_request(self.owner_data["request_id"])
                print("\n[INFO] To approve this request, run:")
                print(f"tester.test_approve_shop({self.owner_data['request_id']})")
        
        # Owner Post-Approval
        print("\n--- OWNER SIGNIN (POST-APPROVAL) ---")
        self.test_owner_signin()
        
        if self.owner_data.get("owner_id"):
            self.test_owner_profile(self.owner_data["owner_id"])
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print(f"\nOwner Data Summary:")
        print(json.dumps({k: v for k, v in self.owner_data.items() if k not in ['access_token', 'admin_token', 'password']}, indent=2))


# Usage
if __name__ == "__main__":
    # Create tester instance
    tester = OwnerAPITester()
    
    print("Owner Portal API Tester Started")
    print("Make sure the FastAPI server is running: uvicorn main:app --reload")
    print("\nAvailable test methods:")
    print("  tester.test_step1_email_signup()")
    print("  tester.test_step2_otp_verification('OTP')")
    print("  tester.test_step3_password_setup('password')")
    print("  tester.test_step4_aadhaar_upload('path/to/image.jpg')")
    print("  tester.test_step5_verify_aadhaar()")
    print("  tester.test_step6_submit_request()")
    print("  tester.test_owner_signin()")
    print("  tester.test_owner_profile(owner_id)")
    print("  tester.test_admin_login('admin_key')")
    print("  tester.test_list_shop_requests(status='pending')")
    print("  tester.test_approve_shop(request_id)")
    print("  tester.test_reject_shop(request_id, 'reason')")
    print("  tester.run_complete_flow_test()")
    print("\nExample:")
    print("  tester.test_step1_email_signup()")
    print("  # Check email for OTP, then:")
    print("  tester.test_step2_otp_verification('123456')")
