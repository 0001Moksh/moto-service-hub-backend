import random
import string
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# In-memory OTP storage (Replace with Redis in production)
OTP_STORAGE: Dict[str, Dict] = {}


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))


def store_otp(email: str, otp: str, expiry_minutes: int = 10) -> bool:
    """Store OTP with expiry time"""
    try:
        OTP_STORAGE[email] = {
            "otp": otp,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=expiry_minutes),
            "attempts": 0
        }
        logger.info(f"OTP stored for {email}")
        return True
    except Exception as e:
        logger.error(f"Error storing OTP: {e}")
        return False


def verify_otp(email: str, otp: str, max_attempts: int = 5) -> bool:
    """Verify OTP"""
    if email not in OTP_STORAGE:
        logger.warning(f"OTP not found for {email}")
        return False
    
    otp_data = OTP_STORAGE[email]
    
    # Check if OTP has expired
    if datetime.now() > otp_data["expires_at"]:
        del OTP_STORAGE[email]
        logger.warning(f"OTP expired for {email}")
        return False
    
    # Check attempts
    if otp_data["attempts"] >= max_attempts:
        del OTP_STORAGE[email]
        logger.warning(f"Max attempts exceeded for {email}")
        return False
    
    # Verify OTP
    if otp_data["otp"] == otp:
        del OTP_STORAGE[email]
        logger.info(f"OTP verified for {email}")
        return True
    
    otp_data["attempts"] += 1
    logger.warning(f"Invalid OTP attempt {otp_data['attempts']} for {email}")
    return False


def clear_otp(email: str) -> bool:
    """Clear OTP"""
    if email in OTP_STORAGE:
        del OTP_STORAGE[email]
        return True
    return False


def get_otp_status(email: str) -> Dict:
    """Get OTP status"""
    if email not in OTP_STORAGE:
        return {"status": "not_found"}
    
    otp_data = OTP_STORAGE[email]
    return {
        "status": "active",
        "attempts": otp_data["attempts"],
        "expires_at": otp_data["expires_at"].isoformat()
    }
