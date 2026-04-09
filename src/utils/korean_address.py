"""Korean Address Manager"""
import random
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import log


class KoreanAddressManager:
    """Manage Korean addresses for payment"""
    
    def __init__(self, address_file: str = "korean_addresses.txt"):
        """
        Initialize address manager
        
        Args:
            address_file: Path to address file (relative to project root)
        """
        self.address_file = Path(__file__).parent.parent.parent / address_file
        self.addresses: List[Dict[str, str]] = []
        self._load_addresses()
    
    def _load_addresses(self):
        """Load addresses from file"""
        try:
            if not self.address_file.exists():
                log.warning(f"⚠ Address file not found: {self.address_file}")
                log.info("💡 Using default Seoul addresses...")
                self._use_default_addresses()
                return
            
            with open(self.address_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse: line1|line2|city|postal_code|state
                parts = line.split('|')
                if len(parts) == 5:
                    self.addresses.append({
                        'line1': parts[0].strip(),
                        'line2': parts[1].strip(),
                        'city': parts[2].strip(),
                        'postal_code': parts[3].strip(),
                        'state': parts[4].strip()
                    })
            
            if self.addresses:
                log.success(f"✓ Loaded {len(self.addresses)} Korean addresses")
            else:
                log.warning("⚠ No valid addresses found, using defaults")
                self._use_default_addresses()
                
        except Exception as e:
            log.error(f"✗ Error loading addresses: {e}")
            self._use_default_addresses()
    
    def _use_default_addresses(self):
        """Use default Seoul addresses as fallback"""
        self.addresses = [
            {
                "line1": "521 Teheran-ro",
                "line2": "Gangnam-gu",
                "city": "Seoul",
                "postal_code": "06164",
                "state": "서울특별시"
            },
            {
                "line1": "123 Sejong-daero",
                "line2": "Jung-gu",
                "city": "Seoul",
                "postal_code": "04524",
                "state": "서울특별시"
            },
            {
                "line1": "456 Gangnam-daero",
                "line2": "Seocho-gu",
                "city": "Seoul",
                "postal_code": "06524",
                "state": "서울특별시"
            }
        ]
    
    def get_random_address(self) -> Dict[str, str]:
        """
        Get a random Korean address
        
        Returns:
            Dict with address fields
        """
        if not self.addresses:
            self._use_default_addresses()
        
        address = random.choice(self.addresses)
        log.info(f"📍 Using address: {address['city']}, {address['line2']}")
        return address
    
    def get_address_by_city(self, city: str) -> Optional[Dict[str, str]]:
        """
        Get a random address from specific city
        
        Args:
            city: City name (Seoul, Busan, etc.)
            
        Returns:
            Dict with address fields or None
        """
        city_addresses = [addr for addr in self.addresses if addr['city'].lower() == city.lower()]
        
        if city_addresses:
            address = random.choice(city_addresses)
            log.info(f"📍 Using {city} address: {address['line2']}")
            return address
        
        log.warning(f"⚠ No addresses found for {city}, using random")
        return self.get_random_address()
    
    def reload_addresses(self):
        """Reload addresses from file"""
        log.info("🔄 Reloading addresses...")
        self.addresses = []
        self._load_addresses()


# Global address manager instance
_address_manager: Optional[KoreanAddressManager] = None


def get_address_manager() -> KoreanAddressManager:
    """Get global address manager instance"""
    global _address_manager
    if _address_manager is None:
        _address_manager = KoreanAddressManager()
    return _address_manager


def get_random_korean_address() -> Dict[str, str]:
    """
    Get a random Korean address (convenience function)
    Tries database first, falls back to file
    
    Returns:
        Dict with address fields
    """
    try:
        from database.repository import KoreanAddressRepository
        address = KoreanAddressRepository.get_random_address(active_only=True)
        
        if address:
            return address
        else:
            log.warning("⚠ No addresses in database, using file")
            return get_address_manager().get_random_address()
    except Exception as e:
        log.warning(f"⚠ Database error: {e}, using file")
        return get_address_manager().get_random_address()
