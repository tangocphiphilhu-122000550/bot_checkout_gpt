"""Browser Helper - Lấy Stripe anti-bot params bằng browser automation"""
import sys
from pathlib import Path
from typing import Optional, Dict
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    log.warning("⚠ Playwright not installed. Install with: pip install playwright && playwright install chromium")


class StripeParamsExtractor:
    """Extract Stripe anti-bot params using browser automation"""
    
    def __init__(self):
        """Initialize extractor"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
    
    def extract_params(
        self,
        checkout_session_id: str,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvc: str,
        billing_name: str,
        billing_email: str,
        timeout: int = 30000
    ) -> Optional[Dict]:
        """
        Extract Stripe params by automating browser
        
        Args:
            checkout_session_id: Stripe checkout session ID
            card_number: Card number
            exp_month: Expiry month
            exp_year: Expiry year
            cvc: CVC
            billing_name: Billing name
            billing_email: Billing email
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with Stripe params or None
        """
        log.info("🌐 Starting browser to extract Stripe params...")
        
        captured_params = {}
        
        try:
            with sync_playwright() as p:
                # Launch browser (headless=False for debugging)
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                # Intercept network requests to capture confirm payload
                def handle_request(route, request):
                    if "confirm" in request.url and request.method == "POST":
                        try:
                            post_data = request.post_data
                            if post_data:
                                # Parse form data
                                from urllib.parse import parse_qs
                                params = parse_qs(post_data)
                                
                                # Extract important params
                                captured_params.update({
                                    'passive_captcha_token': params.get('passive_captcha_token', [None])[0],
                                    'passive_captcha_ekey': params.get('passive_captcha_ekey', [None])[0],
                                    'px3': params.get('px3', [None])[0],
                                    'pxvid': params.get('pxvid', [None])[0],
                                    'pxcts': params.get('pxcts', [None])[0],
                                    'version': params.get('version', [None])[0],
                                    'init_checksum': params.get('init_checksum', [None])[0],
                                    'js_checksum': params.get('js_checksum', [None])[0],
                                    'rv_timestamp': params.get('rv_timestamp', [None])[0]
                                })
                                
                                log.success("✓ Captured Stripe params!")
                        except Exception as e:
                            log.error(f"Error parsing request: {e}")
                    
                    # Continue the request
                    route.continue_()
                
                page.route("**/*", handle_request)
                
                # Navigate to Stripe payment page
                stripe_url = f"https://pay.openai.com/c/pay/{checkout_session_id}"
                log.info(f"📄 Loading: {stripe_url}")
                page.goto(stripe_url, wait_until='networkidle', timeout=timeout)
                
                # Wait for Stripe to load
                log.info("⏳ Waiting for Stripe to initialize...")
                page.wait_for_timeout(3000)
                
                # Fill in payment details
                log.info("📝 Filling payment form...")
                
                try:
                    # Wait for card number iframe
                    card_frame = page.frame_locator('iframe[name*="cardNumber"]').first
                    card_frame.locator('input[name="cardnumber"]').fill(card_number)
                    
                    # Fill expiry
                    exp_frame = page.frame_locator('iframe[name*="cardExpiry"]').first
                    exp_frame.locator('input[name="exp-date"]').fill(f"{exp_month}/{exp_year}")
                    
                    # Fill CVC
                    cvc_frame = page.frame_locator('iframe[name*="cardCvc"]').first
                    cvc_frame.locator('input[name="cvc"]').fill(cvc)
                    
                    # Fill email and name (outside iframe)
                    page.locator('input[name="email"]').fill(billing_email)
                    page.locator('input[name="billingName"]').fill(billing_name)
                    
                    log.info("✓ Form filled")
                    
                    # Wait a bit for anti-bot scripts to run
                    page.wait_for_timeout(2000)
                    
                    # Click submit button (but don't wait for response)
                    log.info("🔘 Clicking submit...")
                    page.locator('button[type="submit"]').click()
                    
                    # Wait for request to be captured
                    page.wait_for_timeout(3000)
                    
                except Exception as e:
                    log.warning(f"⚠ Form filling error (may be OK): {e}")
                
                browser.close()
                
                if captured_params:
                    log.success(f"✓ Extracted {len(captured_params)} params")
                    return captured_params
                else:
                    log.error("✗ No params captured")
                    return None
                
        except Exception as e:
            log.error(f"✗ Browser automation error: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return None


def extract_stripe_params(
    checkout_session_id: str,
    card_number: str,
    exp_month: str,
    exp_year: str,
    cvc: str,
    billing_name: str,
    billing_email: str
) -> Optional[Dict]:
    """
    Helper function to extract Stripe params
    
    Returns:
        Dict with params or None
    """
    if not PLAYWRIGHT_AVAILABLE:
        log.error("✗ Playwright not available")
        return None
    
    extractor = StripeParamsExtractor()
    return extractor.extract_params(
        checkout_session_id=checkout_session_id,
        card_number=card_number,
        exp_month=exp_month,
        exp_year=exp_year,
        cvc=cvc,
        billing_name=billing_name,
        billing_email=billing_email
    )
