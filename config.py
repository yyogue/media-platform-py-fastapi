# -------------------------------
# 🔧 settings.py (Configuration File)
# -------------------------------

# Import BaseSettings from Pydantic — a class that automatically
# reads values from environment variables (.env file)
from pydantic_settings import BaseSettings  # type: ignore

# Import lru_cache to cache the Settings instance (for performance)
from functools import lru_cache


# -------------------------------
# ⚙️ Define the Settings class
# -------------------------------
# This class holds all configuration values your app needs:
# database URLs, secret keys, AWS credentials, token configs, etc.
# BaseSettings will automatically pull these from environment variables.
class Settings(BaseSettings):
    # 🗄️ Database configuration
    database_url: str  # The connection string to ur database (e.g.PostgreSQL)

    # ☁️ AWS S3 configuration
    aws_access_key_id: str          # AWS access key (from IAM user or role)
    aws_secret_access_key: str      # AWS secret key (keep this private!)
    aws_region: str                 # AWS region (e.g. "us-east-1")
    s3_bucket_name: str         # The S3 bucket name where files will be stored

    # 🔒 Security and JWT settings
    secret_key: str           # Your app’s secret key (used for signing tokens)
    algorithm: str = "HS256"      # The JWT signing algorithm (default = HS256)
    access_token_expire_minutes: int = 30  # Expiration time for access tokens

    # Inner class that tells Pydantic where to load environment variables from
    class Config:
        # This means the values will be loaded from a file named ".env"
        # in your project’s root directory
        env_file = ".env"


# -------------------------------
# 💾 Create a cached instance of Settings
# -------------------------------
# lru_cache ensures that Settings() is only loaded *once*.
# This prevents re-reading the .env file on every request.
@lru_cache()
def get_settings() -> Settings:
    # Return a single, cached instance of Settings
    return Settings()
