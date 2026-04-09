"""Payment Bot - Main orchestrator for ChatGPT workspace subscription"""
import sys
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from payment.payment_api import ChatGPTPaymentAPI
from payment.stripe_converter import convert_to_stripe_url
from utils.logger import log

# Try to import browser payment (optional)
try:
    from payment.browser_payment import process_payment_with_browser
    BROWSER_PAYMENT_AVAILABLE = True
except ImportError:
    BROWSER_PAYMENT_AVAILABLE = False
    log.warning("⚠ Browser payment not available. Install playwright: pip install playwright && playwright install chromium")


@dataclass
class PaymentConfig:
    """Payment configuration"""
    workspace_name: str
    card_number: str
    exp_month: str
    exp_year: str
    cvc: str
    billing_name: str
    billing_email: str
    country: str = "KR"
    currency: str = "USD"
    seat_quantity: int = 5
    price_interval: str = "month"
    # Optional: Pre-selected address (if None, will be randomly selected)
    billing_address: Optional[dict] = None


@dataclass
class PaymentResult:
    """Payment result data"""
    success: bool
    workspace_name: Optional[str] = None
    checkout_session_id: Optional[str] = None
    stripe_url: Optional[str] = None
    payment_method_id: Optional[str] = None
    payment_status: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ChatGPTPaymentBot:
    """Main bot for automating ChatGPT workspace subscription payment"""
    
    def __init__(self, access_token: str, cookies: Dict[str, str], use_browser: bool = False):
        """
        Initialize payment bot
        
        Args:
            access_token: Bearer token from registration
            cookies: Session cookies from registration
            use_browser: Use browser automation (set to False to use pure API with anti-bot params)
        """
        self.access_token = access_token
        self.cookies = cookies
        self.payment_api = ChatGPTPaymentAPI(access_token, cookies)
        self.use_browser = use_browser and BROWSER_PAYMENT_AVAILABLE
        
        if use_browser and not BROWSER_PAYMENT_AVAILABLE:
            log.warning("⚠ Browser payment requested but not available. Falling back to API with anti-bot params")
            log.info("💡 Install playwright: pip install playwright && playwright install chromium")
        
    def try_payment_with_card(
        self,
        config: PaymentConfig,
        checkout_session_id: str,
        publishable_key: str,
        expected_amount: int,
        stripe_url: str = None
    ) -> PaymentResult:
        """
        Thử thanh toán với một thẻ cụ thể (dùng cho retry)
        
        Args:
            config: Payment configuration với thông tin thẻ
            checkout_session_id: Session ID đã tạo sẵn
            publishable_key: Publishable key từ session
            expected_amount: Expected amount từ session info
            stripe_url: Stripe URL (optional, sẽ convert nếu không có)
            
        Returns:
            PaymentResult
        """
        from payment.stripe_api import StripePaymentAPI
        
        # Chỉ convert nếu chưa có URL (tránh convert lại mỗi lần retry)
        if not stripe_url:
            stripe_url = convert_to_stripe_url(checkout_session_id)
        
        try:
            # Initialize Stripe API
            stripe_api = StripePaymentAPI(publishable_key, country_code=config.country)
            
            # Step 1: Create payment method
            payment_method_id = stripe_api.create_payment_method(
                card_number=config.card_number,
                exp_month=config.exp_month,
                exp_year=config.exp_year,
                cvc=config.cvc,
                billing_name=config.billing_name,
                billing_email=config.billing_email,
                checkout_session_id=checkout_session_id,
                billing_country=config.country,
                billing_address=config.billing_address
            )
            
            if not payment_method_id:
                return PaymentResult(
                    success=False,
                    workspace_name=config.workspace_name,
                    checkout_session_id=checkout_session_id,
                    stripe_url=stripe_url,
                    error="Failed to create payment method"
                )
            log.info("")
            
            # Step 2: Confirm payment
            payment_result = stripe_api.confirm_payment(
                session_id=checkout_session_id,
                payment_method_id=payment_method_id,
                checkout_session_id=checkout_session_id,
                expected_amount=expected_amount
            )
            
            # Check if payment_result is error dict
            if payment_result and "error" in payment_result:
                error_info = payment_result.get("error", {})
                error_code = error_info.get("code")
                error_message = error_info.get("message")
                
                log.error(f"❌ Payment error: {error_code}")
                log.error(f"   Message: {error_message}")
                
                return PaymentResult(
                    success=False,
                    workspace_name=config.workspace_name,
                    checkout_session_id=checkout_session_id,
                    stripe_url=stripe_url,
                    payment_method_id=payment_method_id,
                    error=f"{error_code}: {error_message}"
                )
            
            if not payment_result:
                return PaymentResult(
                    success=False,
                    workspace_name=config.workspace_name,
                    checkout_session_id=checkout_session_id,
                    stripe_url=stripe_url,
                    payment_method_id=payment_method_id,
                    error="Failed to confirm payment - no response"
                )
            
            # Check payment status
            payment_status = payment_result.get("status")
            payment_payment_status = payment_result.get("payment_status")
            
            # Check if captcha challenge is required
            link_settings = payment_result.get("link_settings", {})
            hcaptcha_site_key = link_settings.get("hcaptcha_site_key")
            
            if hcaptcha_site_key and payment_status != "complete":
                log.warning("")
                log.warning("⚠️ CAPTCHA CHALLENGE DETECTED")
                log.warning("🔴 Thẻ không hợp lệ hoặc bị từ chối")
                log.warning("")
                
                return PaymentResult(
                    success=False,
                    workspace_name=config.workspace_name,
                    checkout_session_id=checkout_session_id,
                    stripe_url=stripe_url,
                    payment_method_id=payment_method_id,
                    error="Captcha challenge required - Card likely invalid or rejected"
                )
            
            log.info("")
            log.info(f"📊 Payment Response:")
            log.info(f"   Status: {payment_status}")
            log.info(f"   Payment Status: {payment_payment_status}")
            
            # Validate success
            is_success = (
                payment_status == "complete" and 
                payment_payment_status in ["paid", "no_payment_required"]
            )
            
            if not is_success:
                log.warning(f"⚠️ Payment may not be complete")
                log.warning(f"   Expected: status='complete' + payment_status='paid'/'no_payment_required'")
                log.warning(f"   Got: status='{payment_status}' + payment_status='{payment_payment_status}'")
            
            log.info("")
            
            return PaymentResult(
                success=is_success,
                workspace_name=config.workspace_name,
                checkout_session_id=checkout_session_id,
                stripe_url=stripe_url,
                payment_method_id=payment_method_id,
                payment_status=f"{payment_status}/{payment_payment_status}"
            )
            
        except Exception as e:
            log.error(f"❌ Error trying payment: {e}")
            return PaymentResult(
                success=False,
                workspace_name=config.workspace_name,
                checkout_session_id=checkout_session_id,
                stripe_url=stripe_url,
                error=str(e)
            )
    
    def process_payment(self, config: PaymentConfig) -> PaymentResult:
        """
        Execute full payment flow
        
        Args:
            config: Payment configuration
            
        Returns:
            PaymentResult with payment details or error
        """
        log.info("=" * 60)
        log.info("💳 STARTING CHATGPT WORKSPACE PAYMENT")
        log.info("=" * 60)
        log.info(f"   Workspace: {config.workspace_name}")
        log.info(f"   Country: {config.country}")
        log.info(f"   Seats: {config.seat_quantity}")
        log.info(f"   Interval: {config.price_interval}")
        log.info("")
        
        try:
            # Step 1: Get available countries (optional validation)
            countries = self.payment_api.get_countries()
            if countries and config.country not in countries:
                log.warning(f"⚠ Country {config.country} not in available list")
            log.info("")
            
            log.info("")
            
            # Step 2: Create checkout session
            checkout_data = self.payment_api.create_checkout_session(
                workspace_name=config.workspace_name,
                country=config.country,
                currency=config.currency,
                seat_quantity=config.seat_quantity,
                price_interval=config.price_interval
            )
            
            if not checkout_data:
                return PaymentResult(
                    success=False,
                    error="Failed to create checkout session"
                )
            
            checkout_session_id = checkout_data.get("checkout_session_id")
            publishable_key = checkout_data.get("publishable_key")
            
            if not checkout_session_id or not publishable_key:
                return PaymentResult(
                    success=False,
                    error="Missing checkout session ID or publishable key"
                )
            
            log.info("")
            
            # Step 3: Convert to Stripe URL
            stripe_url = convert_to_stripe_url(checkout_session_id)
            if not stripe_url:
                return PaymentResult(
                    success=False,
                    checkout_session_id=checkout_session_id,
                    error="Failed to convert to Stripe URL"
                )
            log.info("")
            
            # Step 4: Process payment
            if self.use_browser:
                log.info("🌐 Using browser automation for payment (bypasses anti-bot)...")
                payment_result = process_payment_with_browser(
                    stripe_url=stripe_url,
                    card_number=config.card_number,
                    exp_month=config.exp_month,
                    exp_year=config.exp_year,
                    cvc=config.cvc,
                    billing_name=config.billing_name,
                    billing_email=config.billing_email,
                    headless=True
                )
                
                if payment_result.get('success'):
                    log.info("")
                    log.info("=" * 60)
                    log.success("🎉 PAYMENT COMPLETED SUCCESSFULLY!")
                    log.info("=" * 60)
                    log.info(f"💼 Workspace: {config.workspace_name}")
                    log.info(f"🆔 Session ID: {checkout_session_id}")
                    log.info(f"✅ Status: completed")
                    log.info("=" * 60)
                    
                    return PaymentResult(
                        success=True,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        payment_status="completed"
                    )
                else:
                    return PaymentResult(
                        success=False,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        error=payment_result.get('error', 'Unknown error')
                    )
            else:
                # Use API with anti-bot params (hybrid approach)
                log.info("🔧 Using API payment with anti-bot params (hybrid approach)")
                log.info("💡 Reusing params from successful logs + generating dynamic params")
                
                from payment.stripe_api import StripePaymentAPI
                
                # Step 4: Initialize Stripe API with country code for fingerprinting
                stripe_api = StripePaymentAPI(publishable_key, country_code=config.country)
                
                # Step 4.5: Get expected_amount from checkout session
                log.info("💰 Fetching expected amount from checkout session...")
                session_info = stripe_api.get_checkout_session_info(checkout_session_id)
                
                if session_info:
                    # Try to get amount from invoice
                    invoice = session_info.get("invoice", {})
                    expected_amount = invoice.get("total", 0)
                    subtotal = invoice.get("subtotal", 0)
                    
                    # Check for discounts
                    discount_amounts = invoice.get("total_discount_amounts", [])
                    has_discount = len(discount_amounts) > 0
                    
                    log.info(f"   Subtotal: {subtotal}")
                    log.info(f"   Total: {expected_amount}")
                    log.info(f"   Has discount: {has_discount}")
                    
                    if has_discount:
                        for discount in discount_amounts:
                            discount_amt = discount.get("amount", 0)
                            intervals = discount.get("intervals", 0)
                            log.info(f"   Discount: -{discount_amt} (intervals: {intervals})")
                    
                    log.info(f"   ✅ Using expected_amount: {expected_amount}")
                else:
                    # Fallback to 0 for free trial
                    expected_amount = 0
                    log.warning("   Could not fetch session info, using expected_amount=0")
                
                log.info("")
                
                # Step 5: Create payment method
                payment_method_id = stripe_api.create_payment_method(
                    card_number=config.card_number,
                    exp_month=config.exp_month,
                    exp_year=config.exp_year,
                    cvc=config.cvc,
                    billing_name=config.billing_name,
                    billing_email=config.billing_email,
                    checkout_session_id=checkout_session_id,
                    billing_country=config.country,
                    billing_address=config.billing_address
                )
                
                if not payment_method_id:
                    return PaymentResult(
                        success=False,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        error="Failed to create payment method"
                    )
                log.info("")
                
                # Step 6: Confirm payment with anti-bot params
                payment_result = stripe_api.confirm_payment(
                    session_id=checkout_session_id,
                    payment_method_id=payment_method_id,
                    checkout_session_id=checkout_session_id,
                    expected_amount=expected_amount
                )
                
                # Check if payment_result is error dict
                if payment_result and "error" in payment_result:
                    error_info = payment_result.get("error", {})
                    error_code = error_info.get("code")
                    error_message = error_info.get("message")
                    
                    log.error(f"❌ Payment error: {error_code}")
                    log.error(f"   Message: {error_message}")
                    
                    return PaymentResult(
                        success=False,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        payment_method_id=payment_method_id,
                        error=f"{error_code}: {error_message}"
                    )
                
                if not payment_result:
                    return PaymentResult(
                        success=False,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        payment_method_id=payment_method_id,
                        error="Failed to confirm payment - no response"
                    )
                
                # Check payment status
                payment_status = payment_result.get("status")
                payment_payment_status = payment_result.get("payment_status")
                
                # Check if captcha challenge is required
                link_settings = payment_result.get("link_settings", {})
                hcaptcha_site_key = link_settings.get("hcaptcha_site_key")
                
                if hcaptcha_site_key:
                    log.warning("")
                    log.warning("=" * 60)
                    log.warning("⚠️ CAPTCHA CHALLENGE DETECTED")
                    log.warning("=" * 60)
                    log.warning("🔴 Stripe yêu cầu giải captcha challenge")
                    log.warning("🔴 Điều này thường xảy ra khi:")
                    log.warning("   1. Thẻ không hợp lệ hoặc bị từ chối")
                    log.warning("   2. Thông tin billing không khớp")
                    log.warning("   3. Anti-fraud system phát hiện bất thường")
                    log.warning("")
                    log.warning("💡 Khuyến nghị:")
                    log.warning("   - Thử thẻ khác")
                    log.warning("   - Kiểm tra thông tin billing")
                    log.warning("   - Đổi proxy nếu đang dùng")
                    log.warning("=" * 60)
                    log.warning("")
                    
                    return PaymentResult(
                        success=False,
                        workspace_name=config.workspace_name,
                        checkout_session_id=checkout_session_id,
                        stripe_url=stripe_url,
                        payment_method_id=payment_method_id,
                        error="Captcha challenge required - Card likely invalid or rejected"
                    )
                
                log.info("")
                log.info(f"📊 Payment Response:")
                log.info(f"   Status: {payment_status}")
                log.info(f"   Payment Status: {payment_payment_status}")
                
                # Validate success
                is_success = (
                    payment_status == "complete" and 
                    payment_payment_status in ["paid", "no_payment_required"]
                )
                
                if not is_success:
                    log.warning(f"⚠️ Payment may not be complete")
                    log.warning(f"   Expected: status='complete' + payment_status='paid'/'no_payment_required'")
                    log.warning(f"   Got: status='{payment_status}' + payment_status='{payment_payment_status}'")
                
                log.info("")
                
                # Success!
                log.info("=" * 60)
                if is_success:
                    log.success("🎉 PAYMENT COMPLETED SUCCESSFULLY!")
                else:
                    log.warning("⚠️ PAYMENT STATUS UNCLEAR")
                log.info("=" * 60)
                log.info(f"💼 Workspace: {config.workspace_name}")
                log.info(f"🆔 Session ID: {checkout_session_id}")
                log.info(f"💳 Payment Method: {payment_method_id}")
                log.info(f"✅ Status: {payment_status}")
                log.info(f"💰 Payment Status: {payment_payment_status}")
                log.info("=" * 60)
                
                # Check if workspace was created
                if is_success:
                    log.info("")
                    log.info("🔍 Verifying workspace creation...")
                    log.info(f"   Please check ChatGPT dashboard for workspace: {config.workspace_name}")
                    log.info(f"   URL: https://chatgpt.com/")
                
                return PaymentResult(
                    success=is_success,
                    workspace_name=config.workspace_name,
                    checkout_session_id=checkout_session_id,
                    stripe_url=stripe_url,
                    payment_method_id=payment_method_id,
                    payment_status=f"{payment_status}/{payment_payment_status}"
                )
            
        except Exception as e:
            log.error(f"❌ PAYMENT FAILED: {e}")
            return PaymentResult(
                success=False,
                error=str(e)
            )
        
        finally:
            # Cleanup
            self.close()
    
    def close(self):
        """Close all connections"""
        try:
            self.payment_api.close()
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
