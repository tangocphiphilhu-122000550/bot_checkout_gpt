"""TempMail API service"""
import time
import random
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.http_client import HTTPClient
from utils.logger import log
from utils.config import settings, yaml_config


class TempMailService:
    """Service for creating and managing temporary email addresses"""
    
    def __init__(self):
        self.api_base = yaml_config["tempmail"]["api_base"]
        self.api_key = settings.tempmail_api_key
        self.timeout = yaml_config["tempmail"]["timeout"]
        self.max_otp_attempts = yaml_config["tempmail"]["max_otp_attempts"]
        self.otp_check_interval = yaml_config["tempmail"]["otp_check_interval"]
        self.client = HTTPClient(timeout=self.timeout, use_proxy=settings.use_proxy)
        
    def get_domains(self) -> List[str]:
        """Get available email domains"""
        log.info("📋 Fetching available email domains...")
        
        response = self.client.get(f"{self.api_base}?action=domains")
        data = response.json()
        
        if not data.get("success") or not data.get("domains"):
            raise Exception("Failed to fetch email domains")
        
        domains = data["domains"]
        log.success(f"✓ Found {len(domains)} available domains")
        return domains
    
    def create_email(self, username: Optional[str] = None, domain: Optional[str] = None) -> str:
        """Create a temporary email address"""
        
        # Get random domain if not provided
        if not domain:
            domains = self.get_domains()
            domain = random.choice(domains)
        
        # Generate random username if not provided
        if not username:
            username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        
        log.info(f"📧 Creating temporary email: {username}@{domain}")
        
        response = self.client.get(
            f"{self.api_base}?action=create&api_key={self.api_key}&domain={domain}&user={username}"
        )
        data = response.json()
        
        if not data.get("success") or not data.get("email"):
            raise Exception(f"Failed to create email: {data}")
        
        email = data["email"]
        log.success(f"✓ Email created: {email}")
        return email
    
    def fetch_otp_code(self, email: str) -> Optional[str]:
        """
        Fetch OTP code from email inbox
        Retries multiple times with delay
        """
        log.info(f"⏳ Waiting for OTP code in {email}...")
        
        for attempt in range(1, self.max_otp_attempts + 1):
            log.info(f"📬 Checking inbox... (Attempt {attempt}/{self.max_otp_attempts})")
            
            try:
                response = self.client.get(
                    f"{self.api_base}?action=list&api_key={self.api_key}&email={email}&limit=5"
                )
                data = response.json()
                
                if data.get("success") and data.get("emails"):
                    emails = data["emails"]
                    
                    for mail in emails:
                        subject = mail.get("subject", "")
                        body = mail.get("body", "")
                        from_addr = mail.get("from", "").lower()
                        
                        # Check if email is from OpenAI
                        if "openai" in from_addr or "chatgpt" in subject.lower():
                            # Extract 6-digit OTP from subject or body
                            import re
                            otp_match = re.search(r'\b\d{6}\b', subject) or re.search(r'\b\d{6}\b', body)
                            
                            if otp_match:
                                otp_code = otp_match.group(0)
                                
                                # Skip known non-OTP codes
                                if otp_code != "177010":
                                    log.success(f"✓ OTP code found: {otp_code}")
                                    return otp_code
                
            except Exception as e:
                log.warning(f"⚠ Error checking email: {e}")
            
            # Wait before next attempt
            if attempt < self.max_otp_attempts:
                time.sleep(self.otp_check_interval)
        
        log.error(f"✗ No OTP code received after {self.max_otp_attempts * self.otp_check_interval}s")
        return None
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
