import os
from typing import List

# Environment detection
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"

# CORS Configuration
def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if IS_PRODUCTION:
        # In production, specify your actual domains
        return [
            "https://speaker-kit.testir.xyz",
            "https://speaker-kit.testir.xyz/speaker-kit"
        ]
    else:
        # Development - allow all origins
        return ["*"]

# Server Configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8003))
RELOAD = os.environ.get("RELOAD", "false").lower() == "true"

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./chat.db")

# Security Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-y-change-in-production")

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")

# Static Files Configuration
STATIC_DIR = os.environ.get("STATIC_DIR", "static")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "static/uploads")

# Print configuration for debugging
if __name__ == "__main__":
    print(f"Environment: {ENVIRONMENT}")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Reload: {RELOAD}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"CORS Origins: {get_cors_origins()}") 