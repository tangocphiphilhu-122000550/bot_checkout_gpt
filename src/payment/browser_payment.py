"""Browser-based payment using Playwright to bypass anti-bot protection"""
import sys
from pathlib import Path
from typing import Dict, Optional
import asyncio
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    log.warning("⚠ Playwright not installed. Install with: pip install playwright && playwright install chromium")


class BrowserPaymentBot:
    """Browser-based payment bot using Playwright"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize browser payment bot
        
        Args:
            headless: Run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for browser payment. Install with: pip install playwright && playwright install chromium")
        
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def start(self):
        """Start browser"""
        log.info("🌐 Starting browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        self.page = await self.context.new_page()
        
        # Stealth mode: hide webdriver
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        log.success("✓ Browser started")
    
    async def process_payment(
        self,
        stripe_url: str,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvc: str,
        billing_name: str,
        billing_email: str
    ) -> Dict:
        """
        Process payment using browser automation
        
        Args:
            stripe_url: Stripe payment URL
            card_number: Card number
            exp_month: Expiration month (MM)
            exp_year: Expiration year (YYYY or YY)
            cvc: CVC code
            billing_name: Billing name
            billing_email: Billing email
            
        Returns:
            Payment result dict
        """
        try:
            log.info(f"🌐 Navigating to Stripe payment page...")
            await self.page.goto(stripe_url, wait_until='domcontentloaded', timeout=60000)
            
            log.info("⏳ Waiting for payment form to load...")
            
            # Wait for Stripe iframe to load (more reliable)
            try:
                await self.page.wait_for_selector('iframe[name*="card"]', timeout=45000)
                log.info("✓ Stripe iframe detected")
            except:
                log.warning("⚠ Stripe iframe not found, trying alternative selectors...")
                # Try alternative: wait for any input field
                await self.page.wait_for_selector('input, button[type="submit"]', timeout=30000)
            
            # Wait a bit for all iframes to load
            await self.page.wait_for_timeout(2000)
            
            # Fill card details
            log.info("💳 Filling card details...")
            
            # Card number (in iframe) - try multiple selectors
            try:
                card_frame = self.page.frame_locator('iframe[name*="cardNumber"]').first
                await card_frame.locator('input[name="cardNumber"]').fill(card_number, timeout=10000)
                log.info("✓ Card number filled")
            except Exception as e:
                log.error(f"✗ Failed to fill card number: {e}")
                # Try alternative
                try:
                    card_frame = self.page.frame_locator('iframe[title*="card number"]').first
                    await card_frame.locator('input').first.fill(card_number, timeout=10000)
                    log.info("✓ Card number filled (alternative method)")
                except Exception as e2:
                    log.error(f"✗ Failed alternative card number: {e2}")
                    raise Exception("Cannot fill card number")
            
            # Expiry date (in iframe)
            try:
                expiry_frame = self.page.frame_locator('iframe[name*="cardExpiry"]').first
                await expiry_frame.locator('input[name="cardExpiry"]').fill(f"{exp_month}/{exp_year[-2:]}", timeout=10000)
                log.info("✓ Expiry date filled")
            except Exception as e:
                log.error(f"✗ Failed to fill expiry: {e}")
                try:
                    expiry_frame = self.page.frame_locator('iframe[title*="expir"]').first
                    await expiry_frame.locator('input').first.fill(f"{exp_month}/{exp_year[-2:]}", timeout=10000)
                    log.info("✓ Expiry date filled (alternative method)")
                except Exception as e2:
                    log.error(f"✗ Failed alternative expiry: {e2}")
                    raise Exception("Cannot fill expiry date")
            
            # CVC (in iframe)
            try:
                cvc_frame = self.page.frame_locator('iframe[name*="cardCvc"]').first
                await cvc_frame.locator('input[name="cardCvc"]').fill(cvc, timeout=10000)
                log.info("✓ CVC filled")
            except Exception as e:
                log.error(f"✗ Failed to fill CVC: {e}")
                try:
                    cvc_frame = self.page.frame_locator('iframe[title*="cvc"]').first
                    await cvc_frame.locator('input').first.fill(cvc, timeout=10000)
                    log.info("✓ CVC filled (alternative method)")
                except Exception as e2:
                    log.error(f"✗ Failed alternative CVC: {e2}")
                    raise Exception("Cannot fill CVC")
            
            # Billing name - try multiple selectors
            try:
                await self.page.fill('input[name="billingName"]', billing_name, timeout=5000)
                log.info("✓ Billing name filled")
            except:
                try:
                    await self.page.fill('input[placeholder*="name" i]', billing_name, timeout=5000)
                    log.info("✓ Billing name filled (alternative)")
                except:
                    log.warning("⚠ Could not fill billing name (may not be required)")
            
            # Email (if exists)
            try:
                email_input = await self.page.query_selector('input[name="email"]')
                if email_input:
                    await self.page.fill('input[name="email"]', billing_email, timeout=5000)
                    log.info("✓ Email filled")
            except:
                log.warning("⚠ Could not fill email (may not be required)")
            
            log.info("✅ Submitting payment...")
            
            # Click submit button - try multiple selectors
            try:
                submit_button = await self.page.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()
                    log.info("✓ Submit button clicked")
                else:
                    # Try alternative
                    await self.page.click('button:has-text("Pay")', timeout=5000)
                    log.info("✓ Pay button clicked")
            except Exception as e:
                log.error(f"✗ Failed to click submit: {e}")
                raise Exception("Cannot click submit button")
            
            # Wait for result
            log.info("⏳ Waiting for payment result...")
            
            # Wait for either success or error
            try:
                # Wait for success redirect or error message (longer timeout)
                await self.page.wait_for_url('**/success**', timeout=60000)
                log.success("✓ Payment successful!")
                return {
                    'success': True,
                    'url': self.page.url
                }
            except:
                # Check for error message
                error_element = await self.page.query_selector('[role="alert"]')
                if error_element:
                    error_text = await error_element.text_content()
                    log.error(f"✗ Payment failed: {error_text}")
                    return {
                        'success': False,
                        'error': error_text
                    }
                else:
                    # Check current URL for status
                    current_url = self.page.url
                    if 'success' in current_url.lower() or 'complete' in current_url.lower():
                        log.success("✓ Payment completed (detected from URL)")
                        return {
                            'success': True,
                            'url': current_url
                        }
                    else:
                        # Still processing or unknown state
                        log.warning(f"⚠ Payment status unknown. Current URL: {current_url}")
                        return {
                            'success': False,
                            'error': f'Payment status unknown. URL: {current_url}'
                        }
        
        except Exception as e:
            log.error(f"✗ Browser payment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        log.info("🔒 Browser closed")


def process_payment_with_browser(
    stripe_url: str,
    card_number: str,
    exp_month: str,
    exp_year: str,
    cvc: str,
    billing_name: str,
    billing_email: str,
    headless: bool = True
) -> Dict:
    """
    Synchronous wrapper for browser payment
    
    Args:
        stripe_url: Stripe payment URL
        card_number: Card number
        exp_month: Expiration month
        exp_year: Expiration year
        cvc: CVC code
        billing_name: Billing name
        billing_email: Billing email
        headless: Run in headless mode
        
    Returns:
        Payment result dict
    """
    async def _process():
        bot = BrowserPaymentBot(headless=headless)
        try:
            await bot.start()
            result = await bot.process_payment(
                stripe_url=stripe_url,
                card_number=card_number,
                exp_month=exp_month,
                exp_year=exp_year,
                cvc=cvc,
                billing_name=billing_name,
                billing_email=billing_email
            )
            return result
        finally:
            await bot.close()
    
    return asyncio.run(_process())
