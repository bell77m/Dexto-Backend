import os

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "mydatabase")
DB_PORT = os.getenv("DB_PORT", 3306)

# Secret key for JWT tokens
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")