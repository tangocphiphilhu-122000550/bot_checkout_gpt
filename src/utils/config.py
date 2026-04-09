"""Configuration management"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # TempMail API
    tempmail_api_key: str = Field(alias="TEMPMAIL_API_KEY")
    
    # ChatGPT
    chatgpt_password: str = Field(alias="CHATGPT_PASSWORD")
    
    # Proxy
    use_proxy: bool = Field(default=False, alias="USE_PROXY")
    proxy_file: str = Field(default="proxy.txt", alias="PROXY_FILE")
    
    # Payment Retry
    max_payment_retries: int = Field(default=5, alias="MAX_PAYMENT_RETRIES")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    class Config:
        case_sensitive = False


def load_yaml_config(config_path: str = "../config/settings.yaml") -> Dict[str, Any]:
    """Load YAML configuration file"""
    
    # Try multiple paths
    possible_paths = [
        Path(config_path),
        Path(__file__).parent.parent.parent / "config" / "settings.yaml",
        Path("config/settings.yaml"),
        Path("../config/settings.yaml"),
    ]
    
    for config_file in possible_paths:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    
    # Return default config if file not found
    return {
        "tempmail": {
            "api_base": "https://tempmailapi.io.vn/public_api.php",
            "timeout": 30,
            "max_otp_attempts": 24,
            "otp_check_interval": 5
        },
        "chatgpt": {
            "base_url": "https://chatgpt.com",
            "auth_base_url": "https://auth.openai.com",
            "timeout": 30
        },
        "registration": {
            "first_names": ["James", "Emma", "Liam", "Olivia", "Noah", "Ava"],
            "last_names": ["Smith", "Johnson", "Brown", "Davis", "Wilson"],
            "birth_year_min": 1985,
            "birth_year_max": 2002
        },
        "logging": {
            "level": "INFO",
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            "file": "logs/chatgpt_register_{time}.log"
        }
    }


# Global instances
settings = Settings()
yaml_config = load_yaml_config()
