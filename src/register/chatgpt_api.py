"""ChatGPT Authentication API"""
import uuid
import random
import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.http_client import HTTPClient
from utils.logger import log
from utils.config import yaml_config, settings


class ChatGPTAuthAPI:
    """ChatGPT authentication API client"""
    
    def __init__(self):
        self.chatgpt_base = yaml_config["chatgpt"]["base_url"]
        self.auth_base = yaml_config["chatgpt"]["auth_base_url"]
        self.timeout = yaml_config["chatgpt"]["timeout"]
        self.client = HTTPClient(timeout=self.timeout, use_proxy=settings.use_proxy)
        
        # Generate device identifiers
        self.device_id = str(uuid.uuid4())
        self.auth_session_id = str(uuid.uuid4())
        
    def _make_trace_headers(self) -> Dict[str, str]:
        """Generate DataDog trace headers for tracking"""
        trace_id = str(random.randint(10**17, 10**18 - 1))
        parent_id = str(random.randint(10**17, 10**18 - 1))
        trace_uuid = uuid.uuid4().hex
        
        return {
            'traceparent': f'00-{trace_uuid}-{int(parent_id):016x}-01',
            'tracestate': 'dd=s:1;o:rum',
            'x-datadog-origin': 'rum',
            'x-datadog-sampling-priority': '1',
            'x-datadog-trace-id': trace_id,
            'x-datadog-parent-id': parent_id,
        }
    
    def visit_homepage(self) -> bool:
        """Visit ChatGPT homepage to initialize session"""
        log.info("🌐 Step 1/7: Visiting ChatGPT homepage...")
        
        try:
            response = self.client.get(
                f"{self.chatgpt_base}/",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )
            
            if response.status_code == 200:
                log.success("✓ Homepage visited successfully")
                return True
            else:
                log.error(f"✗ Failed to visit homepage: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"✗ Error visiting homepage: {e}")
            return False
    
    def visit_homepage(self) -> bool:
        """Visit ChatGPT homepage to initialize session"""
        log.info("🌐 Step 1/7: Visiting ChatGPT homepage...")
        
        try:
            response = self.client.get(
                f"{self.chatgpt_base}/",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            
            log.debug(f"Homepage status: {response.status_code}")
            log.debug(f"Cookies after homepage: {len(self.client.get_cookies())} cookies")
            
            if response.status_code == 200:
                log.success("✓ Homepage visited successfully")
                return True
            else:
                log.error(f"✗ Failed to visit homepage: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"✗ Error visiting homepage: {e}")
            return False
    
    def get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from ChatGPT"""
        log.info("🔑 Step 2/7: Fetching CSRF token...")
        
        try:
            response = self.client.get(
                f"{self.chatgpt_base}/api/auth/csrf",
                headers={
                    "Accept": "application/json",
                    "Referer": f"{self.chatgpt_base}/"
                }
            )
            
            # Check status code first
            if response.status_code != 200:
                log.error(f"✗ CSRF request failed with status: {response.status_code}")
                try:
                    log.error(f"Response: {response.text[:200]}")
                except:
                    log.error(f"Response: (binary data)")
                return None
            
            # Try to parse JSON
            try:
                data = response.json()
            except Exception as e:
                log.error(f"✗ Failed to parse JSON response: {e}")
                try:
                    log.error(f"Response text: {response.text[:200]}")
                except:
                    log.error(f"Response: (binary data)")
                return None
            
            csrf_token = data.get("csrfToken")
            
            if csrf_token:
                log.success(f"✓ CSRF token obtained: {csrf_token[:20]}...")
                return csrf_token
            else:
                log.error("✗ No CSRF token in response")
                log.error(f"Response data: {data}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error getting CSRF token: {e}")
            return None
    
    def signin_redirect(self, csrf_token: str, email: str) -> Optional[str]:
        """Get authentication URL"""
        log.info("🔗 Step 3/7: Getting authentication URL...")
        
        try:
            # Query parameters
            params = {
                'prompt': 'login',
                'ext-oai-did': self.device_id,
                'auth_session_logging_id': self.auth_session_id,
                'screen_hint': 'login_or_signup',
                'login_hint': email,
            }
            
            # Body data (form-urlencoded)
            from urllib.parse import urlencode
            body_data = {
                'callbackUrl': f"{self.chatgpt_base}/",
                'csrfToken': csrf_token,
                'json': 'true'
            }
            body_str = urlencode(body_data)
            
            response = self.client.post(
                f"{self.chatgpt_base}/api/auth/signin/openai",
                params=params,
                data=body_str,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "Origin": self.chatgpt_base,
                    "Referer": f"{self.chatgpt_base}/"
                }
            )
            
            data = response.json()
            auth_url = data.get("url")
            
            if auth_url:
                log.success(f"✓ Auth URL obtained: {auth_url[:60]}...")
                return auth_url
            else:
                log.error(f"✗ No auth URL in response: {data}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error getting auth URL: {e}")
            return None
    
    def follow_auth_redirect(self, auth_url: str) -> bool:
        """Follow authentication redirect"""
        log.info("🔗 Following authentication redirect...")
        
        try:
            response = self.client.get(
                auth_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )
            
            log.debug(f"Auth redirect status: {response.status_code}")
            log.debug(f"Auth redirect URL: {response.url}")
            log.debug(f"Cookies after redirect: {len(self.client.get_cookies())} cookies")
            
            if response.status_code == 200:
                log.success("✓ Auth redirect followed successfully")
                return True
            else:
                log.warning(f"⚠ Auth redirect status: {response.status_code}")
                return True  # Continue anyway
                
        except Exception as e:
            log.error(f"✗ Error following auth redirect: {e}")
            return False
    
    def register_account(self, email: str, password: str) -> bool:
        """Register new ChatGPT account"""
        log.info("📝 Step 4/7: Registering account...")
        
        try:
            log.debug(f"Registering with email: {email}")
            log.debug(f"Password length: {len(password)}")
            
            # Check cookies before register
            cookies = self.client.get_cookies()
            log.debug(f"Cookies before register: {len(cookies)} cookies")
            for key in cookies.keys():
                log.debug(f"  Cookie: {key}")
            
            response = self.client.post(
                f"{self.auth_base}/api/accounts/user/register",
                json={
                    "username": email,
                    "password": password
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Referer": f"{self.auth_base}/create-account/password",
                    "Origin": self.auth_base,
                    **self._make_trace_headers()
                }
            )
            
            log.debug(f"Register response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                log.success("✓ Account registered successfully")
                return True
            else:
                try:
                    data = response.json()
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    log.error(f"✗ Register failed ({response.status_code}): {error_msg}")
                    log.debug(f"Full error response: {data}")
                except:
                    log.error(f"✗ Register failed: {response.status_code}")
                    log.debug(f"Response text: {response.text[:500]}")
                return False
                
        except Exception as e:
            log.error(f"✗ Error registering account: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return False
    
    def send_otp(self) -> bool:
        """Send OTP to email"""
        log.info("📧 Step 5/7: Sending OTP to email...")
        
        try:
            response = self.client.get(
                f"{self.auth_base}/api/accounts/email-otp/send",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": f"{self.auth_base}/create-account/password",
                }
            )
            
            log.success("✓ OTP send request completed")
            return True
                
        except Exception as e:
            log.error(f"✗ Error sending OTP: {e}")
            return False
    
    def validate_otp(self, otp_code: str) -> bool:
        """Validate OTP code"""
        log.info("🔢 Step 6/7: Validating OTP code...")
        
        try:
            response = self.client.post(
                f"{self.auth_base}/api/accounts/email-otp/validate",
                json={"code": otp_code},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Referer": f"{self.auth_base}/email-verification",
                    "Origin": self.auth_base,
                    **self._make_trace_headers()
                }
            )
            
            if response.status_code == 200:
                log.success("✓ OTP validated successfully")
                return True
            else:
                try:
                    data = response.json()
                    log.error(f"✗ OTP validation failed ({response.status_code}): {data}")
                except:
                    log.error(f"✗ OTP validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"✗ Error validating OTP: {e}")
            return False
    
    def create_profile(self, name: str, birthdate: str) -> Optional[str]:
        """Create user profile"""
        log.info("📋 Step 7/7: Creating user profile...")
        
        try:
            response = self.client.post(
                f"{self.auth_base}/api/accounts/create_account",
                json={
                    "name": name,
                    "birthdate": birthdate
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Referer": f"{self.auth_base}/about-you",
                    "Origin": self.auth_base,
                    **self._make_trace_headers()
                }
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    continue_url = data.get("continue_url") or data.get("url") or data.get("redirect_url")
                    
                    if continue_url:
                        log.success(f"✓ Profile created, continue URL: {continue_url[:60]}...")
                        return continue_url
                    else:
                        log.success("✓ Profile created successfully")
                        return None
                except:
                    log.success("✓ Profile created successfully")
                    return None
            else:
                log.error(f"✗ Profile creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error creating profile: {e}")
            return None
    
    def follow_continue_url(self, continue_url: str) -> bool:
        """Follow continue URL to complete registration"""
        log.info("🔗 Following continue URL...")
        
        try:
            response = self.client.get(continue_url)
            log.success("✓ Continue URL followed")
            return True
        except Exception as e:
            log.warning(f"⚠ Error following continue URL: {e}")
            return True  # Not critical
    
    def get_cookies(self) -> Dict[str, str]:
        """Get all session cookies"""
        return self.client.get_cookies()
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
