"""ChatGPT Registration Bot - Main orchestrator"""
import random
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from register.email_service import TempMailService
from register.chatgpt_api import ChatGPTAuthAPI
from utils.logger import log
from utils.config import settings, yaml_config


@dataclass
class RegistrationResult:
    """Registration result data"""
    success: bool
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    birthdate: Optional[str] = None
    created_at: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ChatGPTRegistrationBot:
    """Main bot for automating ChatGPT account registration"""
    
    def __init__(self, password: Optional[str] = None):
        """
        Initialize registration bot
        
        Args:
            password: Password for the account (uses env var if not provided)
        """
        self.password = password or settings.chatgpt_password
        self.email_service = TempMailService()
        self.auth_api = ChatGPTAuthAPI()
        
    def _generate_random_name(self) -> str:
        """Generate random full name"""
        first_names = yaml_config["registration"]["first_names"]
        last_names = yaml_config["registration"]["last_names"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return f"{first_name} {last_name}"
    
    def _generate_random_birthdate(self) -> str:
        """Generate random birthdate (YYYY-MM-DD)"""
        year_min = yaml_config["registration"]["birth_year_min"]
        year_max = yaml_config["registration"]["birth_year_max"]
        
        year = random.randint(year_min, year_max)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Safe for all months
        
        return f"{year}-{month:02d}-{day:02d}"
    
    def register(self) -> RegistrationResult:
        """
        Execute full registration flow
        
        Returns:
            RegistrationResult with account details or error
        """
        log.info("=" * 60)
        log.info("🚀 STARTING CHATGPT ACCOUNT REGISTRATION")
        log.info("=" * 60)
        
        try:
            # Generate random profile data
            name = self._generate_random_name()
            birthdate = self._generate_random_birthdate()
            
            log.info(f"👤 Generated profile:")
            log.info(f"   Name: {name}")
            log.info(f"   Birthdate: {birthdate}")
            log.info(f"   Password: {self.password}")
            log.info("")
            
            # Step 1: Create temporary email
            email = self.email_service.create_email()
            log.info("")
            
            # Step 2: Visit homepage FIRST (important!)
            if not self.auth_api.visit_homepage():
                log.warning("⚠ Failed to visit homepage, continuing anyway...")
            log.info("")
            
            # Step 3: Get CSRF token
            csrf_token = self.auth_api.get_csrf_token()
            if not csrf_token:
                return RegistrationResult(
                    success=False,
                    error="Failed to get CSRF token"
                )
            log.info("")
            
            # Step 4: Get authentication URL
            auth_url = self.auth_api.signin_redirect(csrf_token, email)
            if not auth_url:
                return RegistrationResult(
                    success=False,
                    error="Failed to get authentication URL"
                )
            log.info("")
            
            # Step 5: Follow auth redirect
            if not self.auth_api.follow_auth_redirect(auth_url):
                return RegistrationResult(
                    success=False,
                    error="Failed to follow auth redirect"
                )
            log.info("")
            
            # Step 6: Register account
            if not self.auth_api.register_account(email, self.password):
                return RegistrationResult(
                    success=False,
                    error="Failed to register account"
                )
            log.info("")
            
            # Step 7: Send OTP
            if not self.auth_api.send_otp():
                return RegistrationResult(
                    success=False,
                    error="Failed to send OTP"
                )
            log.info("")
            
            # Step 8: Fetch OTP from email
            otp_code = self.email_service.fetch_otp_code(email)
            if not otp_code:
                return RegistrationResult(
                    success=False,
                    email=email,
                    password=self.password,
                    error="Failed to receive OTP code"
                )
            log.info("")
            
            # Step 9: Validate OTP
            if not self.auth_api.validate_otp(otp_code):
                return RegistrationResult(
                    success=False,
                    email=email,
                    password=self.password,
                    error="Failed to validate OTP"
                )
            log.info("")
            
            # Step 10: Create profile
            continue_url = self.auth_api.create_profile(name, birthdate)
            log.info("")
            
            # Step 11: Follow continue URL (if exists)
            if continue_url:
                self.auth_api.follow_continue_url(continue_url)
                log.info("")
            
            # Get session cookies
            cookies = self.auth_api.get_cookies()
            
            # Success!
            log.info("=" * 60)
            log.success("🎉 REGISTRATION COMPLETED SUCCESSFULLY!")
            log.info("=" * 60)
            log.info(f"📧 Email: {email}")
            log.info(f"🔑 Password: {self.password}")
            log.info(f"👤 Name: {name}")
            log.info(f"📅 Birthdate: {birthdate}")
            log.info(f"🍪 Cookies: {len(cookies)} cookies saved")
            log.info("=" * 60)
            
            return RegistrationResult(
                success=True,
                email=email,
                password=self.password,
                name=name,
                birthdate=birthdate,
                created_at=datetime.now().isoformat(),
                cookies=cookies
            )
            
        except Exception as e:
            log.error(f"❌ REGISTRATION FAILED: {e}")
            return RegistrationResult(
                success=False,
                error=str(e)
            )
        
        finally:
            # Cleanup
            self.close()
    
    def close(self):
        """Close all connections"""
        try:
            self.email_service.close()
            self.auth_api.close()
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
