"""ChatGPT Payment API"""
import sys
from pathlib import Path
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.http_client import HTTPClient
from utils.logger import log
from utils.config import yaml_config, settings


class ChatGPTPaymentAPI:
    """ChatGPT payment API client"""
    
    def __init__(self, access_token: str, cookies: Dict[str, str]):
        """
        Initialize payment API
        
        Args:
            access_token: Bearer token from registration
            cookies: Session cookies from registration
        """
        self.chatgpt_base = yaml_config["chatgpt"]["base_url"]
        self.timeout = yaml_config["chatgpt"]["timeout"]
        self.access_token = access_token
        self.client = HTTPClient(timeout=self.timeout, use_proxy=settings.use_proxy)
        self.client.cookies = cookies.copy()
        
    def get_pricing_config(self, currency: str = "USD") -> Optional[Dict]:
        """
        Get pricing configuration for currency
        
        Args:
            currency: Currency code (USD, KRW, etc.)
            
        Returns:
            Pricing config data or None
        """
        log.info(f"💰 Fetching pricing config for {currency}...")
        
        try:
            response = self.client.get(
                f"{self.chatgpt_base}/backend-api/checkout_pricing_config/configs/{currency}",
                headers={
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.access_token}",
                    "Referer": f"{self.chatgpt_base}/"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                log.success(f"✓ Got pricing config for {currency}")
                return data
            else:
                log.error(f"✗ Failed to get pricing config: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error getting pricing config: {e}")
            return None
    
    def get_countries(self) -> Optional[List[str]]:
        """Get available countries for payment"""
        log.info("📋 Fetching available countries...")
        
        try:
            response = self.client.get(
                f"{self.chatgpt_base}/backend-api/checkout_pricing_config/countries",
                headers={
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.access_token}",
                    "Referer": f"{self.chatgpt_base}/"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                countries = data.get("countries", [])
                log.success(f"✓ Found {len(countries)} available countries")
                return countries
            else:
                log.error(f"✗ Failed to get countries: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error getting countries: {e}")
            return None
    
    def create_checkout_session(
        self,
        workspace_name: str,
        country: str = "KR",
        currency: str = "USD",
        seat_quantity: int = 5,
        price_interval: str = "month"
    ) -> Optional[Dict]:
        """
        Create checkout session for workspace subscription
        
        Args:
            workspace_name: Name of the workspace
            country: Country code (default: KR)
            currency: Currency code (default: USD)
            seat_quantity: Number of seats (default: 5)
            price_interval: Billing interval (default: month)
            
        Returns:
            Checkout session data with checkout_session_id, client_secret, etc.
        """
        log.info(f"💳 Creating checkout session for workspace: {workspace_name}")
        
        try:
            payload = {
                "entry_point": "team_workspace_purchase_modal",
                "plan_name": "chatgptteamplan",
                "team_plan_data": {
                    "workspace_name": workspace_name,
                    "price_interval": price_interval,
                    "seat_quantity": seat_quantity
                },
                "billing_details": {
                    "country": country,
                    "currency": currency
                },
                "cancel_url": f"{self.chatgpt_base}/#pricing",
                "promo_campaign": {
                    "promo_campaign_id": "team-1-month-free",
                    "is_coupon_from_query_param": False
                },
                "checkout_ui_mode": "custom"
            }
            
            response = self.client.post(
                f"{self.chatgpt_base}/backend-api/payments/checkout",
                json=payload,
                headers={
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.access_token}",
                    "Origin": self.chatgpt_base,
                    "Referer": f"{self.chatgpt_base}/"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("checkout_session_id")
                client_secret = data.get("client_secret")
                
                log.success(f"✓ Checkout session created: {session_id}")
                log.info(f"   Client secret: {client_secret[:50]}...")
                
                return data
            else:
                log.error(f"✗ Failed to create checkout session: {response.status_code}")
                try:
                    log.error(f"Response: {response.json()}")
                except:
                    log.error(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error creating checkout session: {e}")
            return None
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
