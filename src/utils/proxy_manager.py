"""Proxy Manager - Quản lý proxy rotation và health check"""
import sys
from pathlib import Path
from typing import Optional, List
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log


class ProxyManager:
    """Quản lý proxy với rotation và auto-remove khi die"""
    
    def __init__(self, proxy_file: str = "proxy.txt"):
        """
        Initialize proxy manager
        
        Args:
            proxy_file: Path to proxy file (relative to project root)
        """
        self.proxy_file = Path(__file__).parent.parent.parent / proxy_file
        self.proxies: List[str] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies từ database hoặc file"""
        try:
            # Try to load from database first
            try:
                from database.repository import ProxyRepository
                db_proxies = ProxyRepository.get_all(active_only=True)
                
                if db_proxies:
                    self.proxies = [p.get('proxy_url') for p in db_proxies if p.get('proxy_url')]
                    log.success(f"✓ Đã tải {len(self.proxies)} proxy từ database")
                    return
                else:
                    log.info("ℹ Không có proxy trong database, thử đọc từ file...")
            except Exception as db_error:
                log.warning(f"⚠ Không thể đọc proxy từ database: {db_error}")
                log.info("ℹ Fallback sang đọc từ file...")
            
            # Fallback to file
            if not self.proxy_file.exists():
                log.warning(f"⚠ Proxy file không tồn tại: {self.proxy_file}")
                log.info("💡 Tạo file proxy.txt mẫu...")
                self.proxy_file.write_text(
                    "# Format: username:password@host:port\n"
                    "# Ví dụ:\n"
                    "# user1:pass1@proxy1.example.com:8080\n"
                    "# user2:pass2@proxy2.example.com:8080\n",
                    encoding="utf-8"
                )
                return
            
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter valid proxies (skip comments and empty lines)
            self.proxies = [
                line.strip() 
                for line in lines 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            if self.proxies:
                log.success(f"✓ Đã tải {len(self.proxies)} proxy từ {self.proxy_file.name}")
            else:
                log.warning(f"⚠ Không có proxy nào trong {self.proxy_file.name}")
                
        except Exception as e:
            log.error(f"✗ Lỗi khi đọc proxy: {e}")
            self.proxies = []
    
    def _save_proxies(self):
        """Lưu danh sách proxy hiện tại vào file"""
        try:
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                f.write("# Format: username:password@host:port\n")
                for proxy in self.proxies:
                    f.write(f"{proxy}\n")
            log.info(f"💾 Đã cập nhật {self.proxy_file.name}")
        except Exception as e:
            log.error(f"✗ Lỗi khi lưu proxy file: {e}")
    
    def get_current_proxy(self) -> Optional[str]:
        """
        Lấy proxy hiện tại
        
        Returns:
            Proxy string hoặc None nếu không có proxy
        """
        with self.lock:
            if not self.proxies:
                return None
            
            if self.current_index >= len(self.proxies):
                self.current_index = 0
            
            return self.proxies[self.current_index]
    
    def get_next_proxy(self) -> Optional[str]:
        """
        Chuyển sang proxy tiếp theo
        
        Returns:
            Proxy string hoặc None nếu không có proxy
        """
        with self.lock:
            if not self.proxies:
                return None
            
            self.current_index = (self.current_index + 1) % len(self.proxies)
            proxy = self.proxies[self.current_index]
            log.info(f"🔄 Chuyển sang proxy: {self._mask_proxy(proxy)}")
            return proxy
    
    def mark_proxy_dead(self, proxy: str):
        """
        Đánh dấu proxy die và xóa khỏi danh sách
        
        Args:
            proxy: Proxy string cần xóa
        """
        with self.lock:
            if proxy in self.proxies:
                log.warning(f"💀 Proxy die: {self._mask_proxy(proxy)}")
                self.proxies.remove(proxy)
                
                # Adjust current index if needed
                if self.current_index >= len(self.proxies) and self.proxies:
                    self.current_index = 0
                
                # Save updated list
                self._save_proxies()
                
                if self.proxies:
                    log.info(f"📋 Còn lại {len(self.proxies)} proxy")
                else:
                    log.error("❌ Không còn proxy nào!")
    
    def format_proxy_for_curl_cffi(self, proxy: str) -> Optional[dict]:
        """
        Format proxy cho curl_cffi
        
        Args:
            proxy: Proxy string (username:password@host:port hoặc http://username:password@host:port)
            
        Returns:
            Dict với http và https proxy URLs
        """
        if not proxy:
            return None
        
        try:
            # Remove protocol if already present
            proxy_clean = proxy
            for protocol in ['http://', 'https://', 'socks5://']:
                if proxy.startswith(protocol):
                    proxy_clean = proxy
                    break
            else:
                # No protocol, add http://
                if '@' in proxy:
                    # Has auth: username:password@host:port
                    proxy_clean = f"http://{proxy}"
                else:
                    # No auth: host:port
                    proxy_clean = f"http://{proxy}"
            
            return {
                "http": proxy_clean,
                "https": proxy_clean
            }
        except Exception as e:
            log.error(f"✗ Lỗi format proxy: {e}")
            return None
    
    def _mask_proxy(self, proxy: str) -> str:
        """
        Mask password trong proxy string để log
        
        Args:
            proxy: Proxy string
            
        Returns:
            Masked proxy string
        """
        try:
            # Remove protocol first
            proxy_clean = proxy
            for protocol in ['http://', 'https://', 'socks5://']:
                if proxy.startswith(protocol):
                    proxy_clean = proxy[len(protocol):]
                    break
            
            if '@' in proxy_clean:
                auth, host_port = proxy_clean.split('@', 1)
                if ':' in auth:
                    username, _ = auth.split(':', 1)
                    return f"{username}:****@{host_port}"
            return proxy
        except:
            return proxy
    
    def has_proxies(self) -> bool:
        """Check xem còn proxy không"""
        return len(self.proxies) > 0
    
    def reload_proxies(self):
        """Reload danh sách proxy từ file"""
        log.info("🔄 Đang reload proxy...")
        self._load_proxies()
        self.current_index = 0


# Global proxy manager instance
_proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    """Get global proxy manager instance"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
