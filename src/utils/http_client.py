"""HTTP client with cookie management, Cloudflare bypass, and proxy support"""
from curl_cffi import requests
from typing import Optional, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from proxy_manager import get_proxy_manager
from logger import log


class HTTPClient:
    """HTTP client wrapper with cookie jar, Cloudflare bypass, and proxy rotation"""
    
    def __init__(self, timeout: int = 30, use_proxy: bool = True):
        """
        Initialize HTTP client
        
        Args:
            timeout: Request timeout in seconds
            use_proxy: Có sử dụng proxy hay không
        """
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.cookies = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        # Proxy management
        self.proxy_manager = get_proxy_manager() if use_proxy else None
        self.current_proxy = None
        self.proxy_dict = None
        
        # Set proxy nếu có
        if self.use_proxy and self.proxy_manager and self.proxy_manager.has_proxies():
            self._set_proxy()
    
    def _set_proxy(self):
        """Set proxy cho session"""
        if not self.proxy_manager:
            return
        
        proxy_str = self.proxy_manager.get_current_proxy()
        if proxy_str:
            self.current_proxy = proxy_str
            self.proxy_dict = self.proxy_manager.format_proxy_for_curl_cffi(proxy_str)
            if self.proxy_dict:
                log.info(f"🌐 Sử dụng proxy: {self.proxy_manager._mask_proxy(proxy_str)}")
    
    def _rotate_proxy(self) -> bool:
        """
        Rotate sang proxy tiếp theo
        
        Returns:
            True nếu có proxy mới, False nếu hết proxy
        """
        if not self.proxy_manager:
            return False
        
        # Mark current proxy as dead
        if self.current_proxy:
            self.proxy_manager.mark_proxy_dead(self.current_proxy)
        
        # Get next proxy
        if self.proxy_manager.has_proxies():
            proxy_str = self.proxy_manager.get_next_proxy()
            if proxy_str:
                self.current_proxy = proxy_str
                self.proxy_dict = self.proxy_manager.format_proxy_for_curl_cffi(proxy_str)
                if self.proxy_dict:
                    return True
        
        log.error("❌ Không còn proxy khả dụng!")
        return False
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        GET request với proxy retry
        
        Args:
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        max_retries = 3 if self.use_proxy and self.proxy_manager and self.proxy_manager.has_proxies() else 1
        
        for attempt in range(max_retries):
            try:
                log.debug(f"GET {url} (attempt {attempt + 1}/{max_retries})")
                
                kwargs.setdefault('timeout', self.timeout)
                kwargs.setdefault('impersonate', 'chrome120')
                
                # Merge headers
                headers = self.headers.copy()
                if 'headers' in kwargs:
                    headers.update(kwargs['headers'])
                kwargs['headers'] = headers
                
                # Add cookies
                if self.cookies:
                    kwargs['cookies'] = self.cookies
                
                # Add proxy
                if self.proxy_dict:
                    kwargs['proxies'] = self.proxy_dict
                
                response = requests.get(url, **kwargs)
                
                # Update cookies from response
                if response.cookies:
                    self.cookies.update(dict(response.cookies))
                
                # Check if proxy is working
                if response.status_code in [407, 502, 503, 504]:
                    raise Exception(f"Proxy error: {response.status_code}")
                
                log.debug(f"Response: {response.status_code}")
                return response
                
            except Exception as e:
                if self.use_proxy and attempt < max_retries - 1:
                    log.warning(f"⚠ GET request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if not self._rotate_proxy():
                        raise
                else:
                    raise
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """
        POST request với proxy retry
        
        Args:
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        max_retries = 3 if self.use_proxy and self.proxy_manager and self.proxy_manager.has_proxies() else 1
        
        for attempt in range(max_retries):
            try:
                log.debug(f"POST {url} (attempt {attempt + 1}/{max_retries})")
                
                kwargs.setdefault('timeout', self.timeout)
                kwargs.setdefault('impersonate', 'chrome120')
                
                # Merge headers
                headers = self.headers.copy()
                if 'headers' in kwargs:
                    headers.update(kwargs['headers'])
                kwargs['headers'] = headers
                
                # Add cookies
                if self.cookies:
                    kwargs['cookies'] = self.cookies
                
                # Add proxy
                if self.proxy_dict:
                    kwargs['proxies'] = self.proxy_dict
                
                response = requests.post(url, **kwargs)
                
                # Update cookies from response
                if response.cookies:
                    self.cookies.update(dict(response.cookies))
                
                # Check if proxy is working
                if response.status_code in [407, 502, 503, 504]:
                    raise Exception(f"Proxy error: {response.status_code}")
                
                log.debug(f"Response: {response.status_code}")
                return response
                
            except Exception as e:
                if self.use_proxy and attempt < max_retries - 1:
                    log.warning(f"⚠ POST request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if not self._rotate_proxy():
                        raise
                else:
                    raise
    
    def get_cookies(self) -> Dict[str, str]:
        """Get all cookies as dict"""
        return self.cookies.copy()
    
    def close(self):
        """Close the session"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
