"""Stripe Payment API"""
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.http_client import HTTPClient
from utils.logger import log
from utils.config import settings
from utils.browser_fingerprint import get_browser_fingerprint


class StripePaymentAPI:
    """Stripe payment API client"""
    
    def __init__(self, publishable_key: str, country_code: str = "KR"):
        """
        Initialize Stripe API
        
        Args:
            publishable_key: Stripe publishable key from checkout session
            country_code: Country code for browser fingerprinting (default: KR)
        """
        self.stripe_base = "https://api.stripe.com"
        self.publishable_key = publishable_key
        self.country_code = country_code
        self.client = HTTPClient(timeout=30, use_proxy=settings.use_proxy)
        
        # Generate browser fingerprint
        self.fingerprint = get_browser_fingerprint(country_code)
        
        if settings.use_proxy:
            log.info("🌐 Stripe API will use proxy for requests")
        else:
            log.warning("⚠️ Stripe API NOT using proxy - may get wrong pricing!")
        
        # Log fingerprint info
        fp_info = self.fingerprint.to_dict()
        log.info(f"🖥️ Browser fingerprint: {fp_info['locale']} | {fp_info['timezone']} | {fp_info['screen']}")
    
    def get_checkout_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Lấy thông tin checkout session từ Stripe để biết expected_amount
        
        Args:
            session_id: Checkout session ID (cs_...)
            
        Returns:
            Session info dict hoặc None
        """
        log.info("📋 Fetching checkout session info from Stripe...")
        
        try:
            from urllib.parse import urlencode
            
            # Only send key and eid for GET request
            data = {
                "key": self.publishable_key,
                "eid": "NA"
            }
            
            response = self.client.get(
                f"{self.stripe_base}/v1/payment_pages/{session_id}",
                params=data,
                headers={
                    "Accept": "application/json",
                    "Accept-Language": self.fingerprint.get_accept_language(),
                    "Origin": "https://pay.openai.com",
                    "Referer": "https://pay.openai.com/",
                    "User-Agent": self.fingerprint.get_user_agent()
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract amount from invoice.total (first payment amount with discount)
                invoice = result.get("invoice", {})
                amount_total = invoice.get("total", 0)
                currency = result.get("currency", "usd")
                
                log.success(f"✓ Session info: invoice.total={amount_total} {currency.upper()}")
                
                # Also log recurring amount for reference
                recurring_details = result.get("recurring_details", {})
                recurring_total = recurring_details.get("total", 0)
                if recurring_total != amount_total:
                    log.info(f"   Recurring amount (after trial): {recurring_total} {currency.upper()}")
                
                return result
            else:
                log.error(f"✗ Failed to get session info: {response.status_code}")
                try:
                    log.error(f"Response: {response.json()}")
                except:
                    log.error(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error getting session info: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return None
        
    def create_payment_method(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvc: str,
        billing_name: str,
        billing_email: str,
        checkout_session_id: str,
        billing_country: str = "KR",
        billing_address: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create Stripe payment method
        
        Args:
            card_number: Card number
            exp_month: Expiration month (MM)
            exp_year: Expiration year (YYYY or YY)
            cvc: CVC code
            billing_name: Billing name
            billing_email: Billing email
            checkout_session_id: Checkout session ID for metadata
            billing_country: Billing country code
            billing_address: Optional pre-selected billing address (if None, will be randomly selected)
            
        Returns:
            Payment method ID or None
        """
        log.info("💳 Creating Stripe payment method...")
        
        try:
            from urllib.parse import urlencode
            import uuid
            
            # Convert year format (YYYY -> YY if needed)
            if len(exp_year) == 4:
                exp_year = exp_year[2:]
            
            # Generate tracking IDs
            guid = str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:8]
            muid = str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:6]
            sid = str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:6]
            client_session_id = str(uuid.uuid4())
            
            # Use provided address or get random Korean address
            if billing_address:
                address = billing_address
                log.info(f"   Using provided address: {address['city']}, {address['line2']}")
            else:
                from utils.korean_address import get_random_korean_address
                address = get_random_korean_address()
                log.info(f"   Using random address: {address['city']}, {address['line2']}")
            
            data = {
                "type": "card",
                "card[number]": card_number,
                "card[cvc]": cvc,
                "card[exp_month]": exp_month,
                "card[exp_year]": exp_year,
                "billing_details[name]": billing_name,
                "billing_details[email]": billing_email,
                "billing_details[address][country]": billing_country,
                "billing_details[address][line1]": address["line1"],
                "billing_details[address][line2]": address["line2"],
                "billing_details[address][city]": address["city"],
                "billing_details[address][postal_code]": address["postal_code"],
                "billing_details[address][state]": address["state"],
                "guid": guid,
                "muid": muid,
                "sid": sid,
                "_stripe_version": "2020-08-27;custom_checkout_beta=v1; checkout_server_update_beta=v1; checkout_manual_approval_preview=v1",
                "key": self.publishable_key,
                "payment_user_agent": "stripe.js/d50036e08e; stripe-js-v3/d50036e08e; checkout",
                "client_attribution_metadata[client_session_id]": client_session_id,
                "client_attribution_metadata[checkout_session_id]": checkout_session_id,
                "client_attribution_metadata[merchant_integration_source]": "checkout",
                "client_attribution_metadata[merchant_integration_version]": "custom_checkout",
                "client_attribution_metadata[payment_method_selection_flow]": "automatic",
                "client_attribution_metadata[checkout_config_id]": str(uuid.uuid4())
            }
            
            response = self.client.post(
                f"{self.stripe_base}/v1/payment_methods",
                data=urlencode(data),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "Accept-Language": self.fingerprint.get_accept_language(),
                    "Origin": "https://pay.openai.com",
                    "Referer": "https://pay.openai.com/",
                    "User-Agent": self.fingerprint.get_user_agent()
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                pm_id = result.get("id")
                log.success(f"✓ Payment method created: {pm_id}")
                return pm_id
            else:
                log.error(f"✗ Failed to create payment method: {response.status_code}")
                try:
                    log.error(f"Response: {response.json()}")
                except:
                    log.error(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error creating payment method: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return None
    
    def confirm_payment(
        self,
        session_id: str,
        payment_method_id: str,
        checkout_session_id: str,
        expected_amount: int = 0,
        captcha_token: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Confirm payment with Stripe
        
        Args:
            session_id: Checkout session ID (cs_...)
            payment_method_id: Payment method ID (pm_...)
            checkout_session_id: Full checkout session ID for metadata
            expected_amount: Expected payment amount (0 for trial)
            captcha_token: hCaptcha token (optional)
            
        Returns:
            Payment confirmation result or None
        """
        log.info("✅ Confirming payment with anti-bot params...")
        
        try:
            from urllib.parse import urlencode
            import uuid
            from payment.stripe_params import StripeParamsGenerator
            
            # Generate anti-bot params using hybrid approach
            params_gen = StripeParamsGenerator()
            anti_bot_params = params_gen.get_all_params()
            
            log.info("   Using hybrid anti-bot params (reuse + generate)")
            
            # Generate client session ID
            client_session_id = str(uuid.uuid4())
            
            # Build request data with anti-bot params (NO browser_locale/browser_timezone in confirm)
            data = {
                "eid": "NA",
                "payment_method": payment_method_id,
                "expected_amount": expected_amount,
                "tax_id_collection[purchasing_as_business]": "false",
                "expected_payment_method_type": "card",
                "_stripe_version": "2020-08-27;custom_checkout_beta=v1; checkout_server_update_beta=v1; checkout_manual_approval_preview=v1",
                
                # Anti-bot params from generator
                "guid": anti_bot_params["guid"],
                "muid": anti_bot_params["muid"],
                "sid": anti_bot_params["sid"],
                "version": anti_bot_params["version"],
                "init_checksum": anti_bot_params["init_checksum"],
                "js_checksum": anti_bot_params["js_checksum"],
                "px3": anti_bot_params["px3"],
                "pxvid": anti_bot_params["pxvid"],
                "pxcts": anti_bot_params["pxcts"],
                "passive_captcha_token": anti_bot_params["passive_captcha_token"],
                "passive_captcha_ekey": anti_bot_params["passive_captcha_ekey"],
                "rv_timestamp": anti_bot_params["rv_timestamp"],
                
                # Standard params
                "key": self.publishable_key,
                "referrer": "https://chatgpt.com",
                "client_attribution_metadata[client_session_id]": client_session_id,
                "client_attribution_metadata[checkout_session_id]": checkout_session_id,
                "client_attribution_metadata[merchant_integration_source]": "checkout",
                "client_attribution_metadata[merchant_integration_version]": "custom_checkout",
                "client_attribution_metadata[payment_method_selection_flow]": "automatic",
                "client_attribution_metadata[checkout_config_id]": str(uuid.uuid4())
            }
            
            log.info(f"   Expected amount: {expected_amount}")
            log.info(f"   Using reused params: guid, muid, pxvid, px3, captcha_token")
            log.info(f"   Generated params: sid, pxcts, init_checksum")
            
            response = self.client.post(
                f"{self.stripe_base}/v1/payment_pages/{session_id}/confirm",
                data=urlencode(data),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "Accept-Language": self.fingerprint.get_accept_language(),
                    "Origin": "https://pay.openai.com",
                    "Referer": "https://pay.openai.com/",
                    "User-Agent": self.fingerprint.get_user_agent()
                }
            )
            
            log.debug(f"📤 Request sent to: /v1/payment_pages/{session_id}/confirm")
            log.debug(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                log.success(f"✓ Payment confirmed: {status}")
                return result
            else:
                log.error(f"✗ Failed to confirm payment: {response.status_code}")
                try:
                    error_data = response.json()
                    log.error(f"Response: {error_data}")
                    
                    # Debug: Show which params we sent
                    log.debug("📋 Params sent:")
                    log.debug(f"   - expected_amount: {data.get('expected_amount')}")
                    log.debug(f"   - payment_method: {data.get('payment_method')}")
                    log.debug(f"   - Has px3: {bool(data.get('px3'))}")
                    log.debug(f"   - Has passive_captcha_token: {bool(data.get('passive_captcha_token'))}")
                    log.debug(f"   - Has rv_timestamp: {bool(data.get('rv_timestamp'))}")
                    
                    return error_data
                except:
                    log.error(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            log.error(f"✗ Error confirming payment: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return None
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
