"""Helper functions for token management"""
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.http_client import HTTPClient
from utils.logger import log
from utils.config import yaml_config


def get_access_token(cookies: Dict[str, str]) -> Optional[str]:
    """
    Get access token from ChatGPT session
    
    Args:
        cookies: Session cookies from registration
        
    Returns:
        Access token (Bearer token) or None
    """
    log.info("🔑 Fetching access token from session...")
    
    try:
        chatgpt_base = yaml_config["chatgpt"]["base_url"]
        client = HTTPClient(timeout=30)
        client.cookies = cookies.copy()
        
        response = client.get(
            f"{chatgpt_base}/api/auth/session",
            headers={
                "Accept": "application/json",
                "Referer": f"{chatgpt_base}/"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("accessToken")
            
            if access_token:
                log.success(f"✓ Access token obtained: {access_token[:50]}...")
                return access_token
            else:
                log.error("✗ No access token in session response")
                return None
        else:
            log.error(f"✗ Failed to get session: {response.status_code}")
            return None
            
    except Exception as e:
        log.error(f"✗ Error getting access token: {e}")
        return None
