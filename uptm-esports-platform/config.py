import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uptm-esports-fallback-key-2026')
    
    # SQLite Database stored in instance directory
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'uptm_esports.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security & Admin Settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@uptm.edu.my')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@UPTM2026!')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
    
    # Institutional Email Validation
    ALLOWED_EMAIL_DOMAINS = [
        d.strip().lower() 
        for d in os.environ.get('ALLOWED_EMAIL_DOMAINS', 'student.uptm.edu.my,uptm.edu.my').split(',')
        if d.strip()
    ]
