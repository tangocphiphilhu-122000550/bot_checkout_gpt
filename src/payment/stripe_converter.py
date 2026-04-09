"""Stripe link converter - Convert ChatGPT checkout session to Stripe payment URL"""
import re
from typing import Optional
from utils.logger import log


# Sample suffix from pastel_link_converter_html/popup.js
SAMPLE_SUFFIX = "#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSd2cGd2ZndsdXFsamtQa2x0cGBrYHZ2QGtkZ2lgYSc%2FY2RpdmApJ3BsSGphYCc%2FJ2ZwdnFqaCd4JSUl"

TARGET_PREFIX = "https://pay.openai.com/c/pay/"


def extract_token(value: str) -> Optional[str]:
    """
    Extract cs_ token from various input formats
    
    Args:
        value: Input string (can be full URL, token, or mixed text)
        
    Returns:
        Extracted token or None
    """
    if not value:
        return None
        
    trimmed = value.strip()
    if not trimmed:
        return None
    
    # If starts with cs_, extract until first delimiter
    if trimmed.startswith("cs_"):
        return re.split(r'[?#\s]', trimmed)[0]
    
    # Otherwise search for cs_ pattern
    match = re.search(r'cs_[A-Za-z0-9_]+', trimmed)
    return match.group(0) if match else None


def convert_to_stripe_url(checkout_session_id: str) -> Optional[str]:
    """
    Convert checkout session ID to Stripe payment URL
    
    Args:
        checkout_session_id: Checkout session ID from ChatGPT (starts with cs_)
        
    Returns:
        Stripe payment URL or None
    """
    token = extract_token(checkout_session_id)
    
    if not token:
        log.error("✗ Invalid checkout session ID - must start with cs_")
        return None
    
    stripe_url = f"{TARGET_PREFIX}{token}{SAMPLE_SUFFIX}"
    log.success(f"✓ Converted to Stripe URL: {stripe_url[:80]}...")
    
    return stripe_url
