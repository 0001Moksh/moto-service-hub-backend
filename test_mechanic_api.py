"""
Mechanic Portal API Testing Guide
Run this after starting the FastAPI server with: uvicorn main:app --reload

This test script covers:
1. Owner inviting mechanics
2. Mechanic accepting invitation
3. Mechanic signup (password + Aadhaar)
4. Mechanic signin
5. Owner managing mechanics
"""

import requests
import json
from typing import Dict, Any, Optional
import time

BASE_URL = "http://localhost:8000"

class MechanicAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.owner_data = {}
        self.mechanic_data = {}
        
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
    
    # ==================== OWNER FLOW ====================
    
    def owner_login(self, owner_id: int = 1) -> bool:
        """Login owner (simulated - use actual JWT from signup)"""
        # For testing, we'll use owner_id directly
        # In real scenario, use JWT token from owner signin
        self.owner_data["owner_id"] = owner_id
        self.owner_data["access_token"] = "simulated_token"
        print(f"\nOwner logged in with ID: {owner_id}")
        return True
    
    def owner_invite_mechanic(self, mechanic_email: str, mechanic_name: str) -> Optional[str]:
        """Owner invites a mechanic"""
        url = f"{self.base_url}/api/owner/invite-mechanic"
        params = {"owner_id": self.owner_data.get("owner_id", 1)}
        payload = {
            "mechanic_email": mechanic_email,
            "mechanic_name": mechanic_name
        }
        
        response = self.session.post(url, json=payload, params=params)
        success = self.print_response(f"Owner: Invite Mechanic ({mechanic_email})", response)
        
        if success and response.json().get("success"):
            invitation_token = response.json().get("invitation_token")
            self.mechanic_data["invitation_token"] = invitation_token
            self.mechanic_data["email"] = mechanic_email
            self.mechanic_data["name"] = mechanic_name
            return invitation_token
        return None
    
    def owner_list_mechanics(self) -> bool:
        """Owner: List all mechanics in shop"""
        url = f"{self.base_url}/api/mechanic/shop/{{owner_id}}/mechanics"
        owner_id = self.owner_data.get("owner_id", 1)
        url = url.replace("{owner_id}", str(owner_id))
        
        response = self.session.get(url)
        return self.print_response("Owner: List Mechanics", response, expect_200=False)
    
    def owner_remove_mechanic(self, mechanic_id: int) -> bool:
        """Owner: Remove mechanic from shop"""
        url = f"{self.base_url}/api/mechanic/remove"
        params = {"owner_id": self.owner_data.get("owner_id", 1)}
        payload = {"mechanic_id": mechanic_id}
        
        response = self.session.delete(url, json=payload, params=params)
        return self.print_response(f"Owner: Remove Mechanic (ID={mechanic_id})", response, expect_200=False)
    
    # ==================== MECHANIC SIGNUP FLOW ====================
    
    def mechanic_accept_invitation(self, invitation_token: str = None) -> bool:
        """Mechanic Step 1: Accept invitation"""
        if not invitation_token:
            invitation_token = self.mechanic_data.get("invitation_token")
        
        url = f"{self.base_url}/api/mechanic/signup/step1"
        payload = {"invitation_token": invitation_token}
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Mechanic Step 1: Accept Invitation", response)
        
        if success and response.json().get("success"):
            self.mechanic_data["step"] = 1
            self.mechanic_data["invitation_token"] = invitation_token
        return success
    
    def mechanic_set_password(self, password: str = "MechanicPassword123", invitation_token: str = None) -> bool:
        """Mechanic Step 2: Set password"""
        if not invitation_token:
            invitation_token = self.mechanic_data.get("invitation_token")
        
        url = f"{self.base_url}/api/mechanic/signup/step2"
        payload = {
            "invitation_token": invitation_token,
            "password": password
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Mechanic Step 2: Set Password", response)
        
        if success and response.json().get("success"):
            self.mechanic_data["password"] = password
            self.mechanic_data["step"] = 2
        return success
    
    def mechanic_upload_aadhaar(self, image_path: str = None, invitation_token: str = None) -> bool:
        """Mechanic Step 3a: Upload Aadhaar"""
        if not invitation_token:
            invitation_token = self.mechanic_data.get("invitation_token")
        
        url = f"{self.base_url}/api/mechanic/signup/step3-upload-aadhaar"
        
        # Check if real image exists
        if image_path and __import__('os').path.exists(image_path):
            with open(image_path, 'rb') as f:
                files = {'file': f}
                data = {'invitation_token': invitation_token}
                response = self.session.post(url, data=data, files=files)
        else:
            # Use dummy test without real image
            print("\n[INFO] Mechanic Step 3a: Upload Aadhaar - Skipped (no image provided)")
            print("To test, call with image_path parameter: tester.mechanic_upload_aadhaar('path/to/aadhaar.jpg')")
            self.mechanic_data["aadhaar_extracted"] = {
                "name": "Raj Kumar",
                "gender": "M",
                "dob": "1995-05-20",
                "aadhaar_number": "1234-5678-9012"
            }
            self.mechanic_data["step"] = 3
            return True
        
        success = self.print_response("Mechanic Step 3a: Upload Aadhaar", response)
        
        if success and response.json().get("success"):
            self.mechanic_data["aadhaar_extracted"] = response.json().get("extracted_data", {})
            self.mechanic_data["step"] = 3
        return success
    
    def mechanic_verify_aadhaar(self, invitation_token: str = None) -> bool:
        """Mechanic Step 3b: Verify Aadhaar"""
        if not invitation_token:
            invitation_token = self.mechanic_data.get("invitation_token")
        
        url = f"{self.base_url}/api/mechanic/signup/step3-verify-aadhaar"
        
        # Use extracted data or defaults
        aadhaar_data = self.mechanic_data.get("aadhaar_extracted", {
            "name": "Raj Kumar",
            "gender": "M",
            "dob": "1995-05-20",
            "aadhaar_number": "1234-5678-9012"
        })
        
        payload = {
            "invitation_token": invitation_token,
            "mechanic_name": aadhaar_data.get("name", self.mechanic_data.get("name", "Raj Kumar")),
            "gender": aadhaar_data.get("gender", "M"),
            "dob": aadhaar_data.get("dob", "1995-05-20"),
            "aadhaar_number": aadhaar_data.get("aadhaar_number", "1234-5678-9012")
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Mechanic Step 3b: Verify Aadhaar", response)
        
        if success and response.json().get("success"):
            self.mechanic_data["aadhaar_verified"] = True
            self.mechanic_data["mechanic_id"] = response.json().get("mechanic_id")
            self.mechanic_data["step"] = 3
        return success
    
    # ==================== MECHANIC AUTHENTICATION ====================
    
    def mechanic_signin(self, email: str = None, password: str = None) -> bool:
        """Mechanic signin"""
        if not email:
            email = self.mechanic_data.get("email")
        if not password:
            password = self.mechanic_data.get("password", "MechanicPassword123")
        
        url = f"{self.base_url}/api/mechanic/signin"
        payload = {
            "email": email,
            "password": password
        }
        
        response = self.session.post(url, json=payload)
        success = self.print_response("Mechanic: Signin", response)
        
        if success and response.json().get("success"):
            token = response.json().get("access_token")
            self.mechanic_data["access_token"] = token
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            mechanic = response.json().get("mechanic", {})
            self.mechanic_data["mechanic_id"] = mechanic.get("mechanic_id")
        return success
    
    def mechanic_get_profile(self, mechanic_id: int = None) -> bool:
        """Get mechanic profile"""
        if not mechanic_id:
            mechanic_id = self.mechanic_data.get("mechanic_id")
        
        if not mechanic_id:
            print("[SKIP] Mechanic profile - no mechanic ID available")
            return False
        
        url = f"{self.base_url}/api/mechanic/profile/{mechanic_id}"
        
        response = self.session.get(url)
        return self.print_response(f"Mechanic: Get Profile (ID={mechanic_id})", response, expect_200=False)
    
    # ==================== COMPLETE FLOW TESTS ====================
    
    def run_owner_invite_flow_test(self, owner_id: int = 1):
        """Test owner inviting mechanic"""
        print("\n" + "="*60)
        print("MECHANIC PORTAL - OWNER INVITE FLOW TEST")
        print("="*60)
        
        # Owner login
        self.owner_login(owner_id)
        
        # Owner invites mechanic
        mechanic_email = f"mechanic_test_{int(time.time())}@example.com"
        mechanic_name = "Test Mechanic"
        
        self.owner_invite_mechanic(mechanic_email, mechanic_name)
        
        # Owner lists mechanics
        self.owner_list_mechanics()
        
        print("\n" + "="*60)
        print("OWNER INVITE FLOW TEST COMPLETE")
        print("="*60)
    
    def run_mechanic_signup_flow_test(self, invitation_token: str = None):
        """Test complete mechanic signup flow"""
        print("\n" + "="*60)
        print("MECHANIC PORTAL - COMPLETE SIGNUP FLOW TEST")
        print("="*60)
        
        if invitation_token:
            self.mechanic_data["invitation_token"] = invitation_token
        
        if not self.mechanic_data.get("invitation_token"):
            print("[ERROR] No invitation token provided. Run owner_invite_flow_test first.")
            return
        
        print(f"\nUsing invitation token: {self.mechanic_data['invitation_token'][:20]}...")
        
        # Step 1: Accept invitation
        if not self.mechanic_accept_invitation():
            print("Failed at Step 1")
            return
        
        # Step 2: Set password
        if not self.mechanic_set_password():
            print("Failed at Step 2")
            return
        
        # Step 3a: Upload Aadhaar (simulated)
        if not self.mechanic_upload_aadhaar():
            print("Failed at Step 3a")
            return
        
        # Step 3b: Verify Aadhaar
        if not self.mechanic_verify_aadhaar():
            print("Failed at Step 3b")
            return
        
        # Signin
        if self.mechanic_signin():
            # Get profile
            self.mechanic_get_profile()
        
        print("\n" + "="*60)
        print("MECHANIC SIGNUP FLOW TEST COMPLETE")
        print("="*60)
        print(f"\nMechanic Data Summary:")
        print(json.dumps({k: v for k, v in self.mechanic_data.items() if k not in ['access_token', 'password']}, indent=2))


# Usage
if __name__ == "__main__":
    # Create tester instance
    tester = MechanicAPITester()
    
    print("Mechanic Portal API Tester Started")
    print("Make sure the FastAPI server is running: uvicorn main:app --reload")
    print("\nAvailable test methods:")
    print("  # Owner flow")
    print("  tester.owner_login(owner_id=1)")
    print("  tester.owner_invite_mechanic('email@example.com', 'Name')")
    print("  tester.owner_list_mechanics()")
    print("  tester.owner_remove_mechanic(mechanic_id)")
    print()
    print("  # Mechanic signup flow")
    print("  tester.mechanic_accept_invitation('token')")
    print("  tester.mechanic_set_password('password', 'token')")
    print("  tester.mechanic_upload_aadhaar('path/to/image.jpg', 'token')")
    print("  tester.mechanic_verify_aadhaar('token')")
    print("  tester.mechanic_signin('email', 'password')")
    print("  tester.mechanic_get_profile(mechanic_id)")
    print()
    print("  # Complete flows")
    print("  tester.run_owner_invite_flow_test(owner_id=1)")
    print("  tester.run_mechanic_signup_flow_test('invitation_token')")
    print()
    print("Example workflow:")
    print("  1. tester.run_owner_invite_flow_test(owner_id=1)")
    print("  2. Copy invitation_token from response")
    print("  3. tester.run_mechanic_signup_flow_test('the-copied-token')")
