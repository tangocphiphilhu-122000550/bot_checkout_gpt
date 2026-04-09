"""
Browser Fingerprinting Module
Generates realistic browser fingerprint data to make bot look like real user
"""
import random
from typing import Dict
from datetime import datetime


class BrowserFingerprint:
    """Generate realistic browser fingerprint"""
    
    # Common browser locales
    LOCALES = [
        "en-US",
        "en-GB", 
        "ko-KR",  # Korean
        "ja-JP",  # Japanese
        "zh-CN",  # Chinese
        "vi-VN",  # Vietnamese
    ]
    
    # Timezones by region
    TIMEZONES = {
        "KR": "Asia/Seoul",
        "JP": "Asia/Tokyo",
        "CN": "Asia/Shanghai",
        "VN": "Asia/Ho_Chi_Minh",
        "US": "America/New_York",
        "GB": "Europe/London",
    }
    
    # Screen resolutions (common ones)
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},  # Full HD
        {"width": 1366, "height": 768},   # Laptop
        {"width": 1536, "height": 864},   # Laptop
        {"width": 2560, "height": 1440},  # 2K
        {"width": 1440, "height": 900},   # MacBook
        {"width": 1280, "height": 720},   # HD
    ]
    
    # User agents (Chrome on Windows)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, country_code: str = "KR"):
        """
        Initialize browser fingerprint
        
        Args:
            country_code: Country code (KR, US, JP, etc.)
        """
        self.country_code = country_code
        self._fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> Dict:
        """Generate complete browser fingerprint"""
        
        # Select locale based on country
        if self.country_code == "KR":
            locale = "ko-KR"
        elif self.country_code == "JP":
            locale = "ja-JP"
        elif self.country_code == "CN":
            locale = "zh-CN"
        elif self.country_code == "VN":
            locale = "vi-VN"
        else:
            locale = random.choice(["en-US", "en-GB"])
        
        # Get timezone for country
        timezone = self.TIMEZONES.get(self.country_code, "Asia/Seoul")
        
        # Random screen resolution
        screen = random.choice(self.SCREEN_RESOLUTIONS)
        
        # Random user agent
        user_agent = random.choice(self.USER_AGENTS)
        
        # Color depth (common values)
        color_depth = random.choice([24, 32])
        
        # Pixel ratio (common values)
        pixel_ratio = random.choice([1, 1.25, 1.5, 2])
        
        # Hardware concurrency (CPU cores)
        hardware_concurrency = random.choice([4, 6, 8, 12, 16])
        
        # Device memory (GB)
        device_memory = random.choice([4, 8, 16, 32])
        
        # Platform
        platform = "Win32"
        
        # Languages (based on locale)
        if locale.startswith("ko"):
            languages = ["ko-KR", "ko", "en-US", "en"]
        elif locale.startswith("ja"):
            languages = ["ja-JP", "ja", "en-US", "en"]
        elif locale.startswith("zh"):
            languages = ["zh-CN", "zh", "en-US", "en"]
        elif locale.startswith("vi"):
            languages = ["vi-VN", "vi", "en-US", "en"]
        else:
            languages = ["en-US", "en"]
        
        return {
            "locale": locale,
            "timezone": timezone,
            "timezone_offset": self._get_timezone_offset(timezone),
            "screen_width": screen["width"],
            "screen_height": screen["height"],
            "color_depth": color_depth,
            "pixel_ratio": pixel_ratio,
            "hardware_concurrency": hardware_concurrency,
            "device_memory": device_memory,
            "platform": platform,
            "user_agent": user_agent,
            "languages": languages,
            "do_not_track": None,  # Most users don't enable this
            "cookies_enabled": True,
        }
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """
        Get timezone offset in minutes
        
        Args:
            timezone: Timezone string (e.g., "Asia/Seoul")
            
        Returns:
            Offset in minutes (negative for east of UTC)
        """
        # Common timezone offsets (in minutes)
        offsets = {
            "Asia/Seoul": -540,      # UTC+9
            "Asia/Tokyo": -540,      # UTC+9
            "Asia/Shanghai": -480,   # UTC+8
            "Asia/Ho_Chi_Minh": -420, # UTC+7
            "America/New_York": 300,  # UTC-5 (EST)
            "Europe/London": 0,       # UTC+0
        }
        return offsets.get(timezone, -540)
    
    def get_browser_init_params(self) -> Dict:
        """
        Get browser init params for Stripe API
        
        Returns:
            Dict with browser_locale and browser_timezone
        """
        return {
            "browser_locale": self._fingerprint["locale"],
            "browser_timezone": self._fingerprint["timezone"],
        }
    
    def get_full_fingerprint(self) -> Dict:
        """
        Get complete browser fingerprint
        
        Returns:
            Dict with all fingerprint data
        """
        return self._fingerprint.copy()
    
    def get_user_agent(self) -> str:
        """Get user agent string"""
        return self._fingerprint["user_agent"]
    
    def get_accept_language(self) -> str:
        """
        Get Accept-Language header value
        
        Returns:
            Accept-Language header string
        """
        languages = self._fingerprint["languages"]
        # Format: "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        result = []
        q = 1.0
        for lang in languages:
            if q == 1.0:
                result.append(lang)
            else:
                result.append(f"{lang};q={q:.1f}")
            q -= 0.1
            if q < 0.7:
                break
        return ",".join(result)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "locale": self._fingerprint["locale"],
            "timezone": self._fingerprint["timezone"],
            "screen": f"{self._fingerprint['screen_width']}x{self._fingerprint['screen_height']}",
            "platform": self._fingerprint["platform"],
            "languages": ",".join(self._fingerprint["languages"]),
        }


# Singleton instance for reuse across requests
_fingerprint_cache = {}


def get_browser_fingerprint(country_code: str = "KR", force_new: bool = False) -> BrowserFingerprint:
    """
    Get browser fingerprint (cached per country)
    
    Args:
        country_code: Country code
        force_new: Force generate new fingerprint
        
    Returns:
        BrowserFingerprint instance
    """
    if force_new or country_code not in _fingerprint_cache:
        _fingerprint_cache[country_code] = BrowserFingerprint(country_code)
    return _fingerprint_cache[country_code]
