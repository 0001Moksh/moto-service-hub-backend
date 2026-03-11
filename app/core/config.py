import os
import sys
import logging
from dotenv import load_dotenv
from typing import Optional

load_dotenv('.env.local')

# Fix logging encoding for Windows
if sys.platform == 'win32':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )

class Settings:
    # App Settings
    APP_NAME = os.getenv("NEXT_PUBLIC_APP_NAME", "Moto Service Hub")
    APP_VERSION = "1.0.0"
    DEBUG = True
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # JWT Settings
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database Settings (Supabase)
    SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing Supabase credentials in .env.local")
    
    # Email Settings (SMTP)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    
    # OTP Settings
    OTP_EXPIRY_MINUTES = 10
    OTP_LENGTH = 6
    
    # Groq API Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    # Admin Settings
    ADMIN_EMAIL = os.getenv("NEXT_PUBLIC_ADMIN_MAIL", "admin@example.com")
    ADMIN_KEY = os.getenv("ADMIN_KEY", "")
    
    # Azure Settings
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")


settings = Settings()
