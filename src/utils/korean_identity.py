"""Korean identity generator - Get random Korean identity"""
import random
from typing import Dict, Optional
from .http_client import HTTPClient
from .logger import log


# Fallback Korean names if API fails
KOREAN_FIRST_NAMES = [
    "민준", "서준", "예준", "도윤", "시우", "주원", "하준", "지호", "지우", "준서",
    "서연", "서윤", "지우", "서현", "민서", "하은", "지유", "수아", "지민", "윤서"
]

KOREAN_LAST_NAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"
]


def generate_korean_name() -> str:
    """
    Generate random Korean name
    
    Returns:
        Korean name (Last + First)
    """
    last_name = random.choice(KOREAN_LAST_NAMES)
    first_name = random.choice(KOREAN_FIRST_NAMES)
    return f"{last_name}{first_name}"


def romanize_korean_name(korean_name: str) -> str:
    """
    Simple romanization of Korean name
    (For real use, should use proper romanization API)
    
    Returns:
        Romanized name
    """
    # Simple mapping (not accurate, just for demo)
    romanization_map = {
        "김": "Kim", "이": "Lee", "박": "Park", "최": "Choi", "정": "Jung",
        "강": "Kang", "조": "Cho", "윤": "Yoon", "장": "Jang", "임": "Lim",
        "한": "Han", "오": "Oh", "서": "Seo", "신": "Shin", "권": "Kwon",
        "황": "Hwang", "안": "Ahn", "송": "Song", "류": "Ryu", "홍": "Hong",
        "민준": "Minjun", "서준": "Seojun", "예준": "Yejun", "도윤": "Doyun",
        "시우": "Siwoo", "주원": "Juwon", "하준": "Hajun", "지호": "Jiho",
        "지우": "Jiwoo", "준서": "Junseo", "서연": "Seoyeon", "서윤": "Seoyoon",
        "서현": "Seohyun", "민서": "Minseo", "하은": "Haeun", "지유": "Jiyu",
        "수아": "Sua", "지민": "Jimin", "윤서": "Yunseo"
    }
    
    # Try to romanize
    for korean, roman in romanization_map.items():
        korean_name = korean_name.replace(korean, roman + " ")
    
    return korean_name.strip()


def get_korean_identity_from_api() -> Optional[Dict[str, str]]:
    """
    Get random Korean identity from API
    Using randomuser.me API with Korean nationality
    
    Returns:
        Dict with name, email, phone or None if failed
    """
    try:
        log.info("🌐 Đang lấy thông tin Korean từ API...")
        
        client = HTTPClient(timeout=10)
        response = client.get(
            "https://randomuser.me/api/",
            params={"nat": "kr", "inc": "name,email,phone"}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if results:
                user = results[0]
                name_data = user.get("name", {})
                
                # Combine first and last name
                full_name = f"{name_data.get('first', '')} {name_data.get('last', '')}".strip()
                
                identity = {
                    "name": full_name,
                    "email": user.get("email", ""),
                    "phone": user.get("phone", "")
                }
                
                log.success(f"✓ Đã lấy thông tin: {identity['name']}")
                return identity
        
        log.warning("⚠ API không trả về dữ liệu hợp lệ")
        return None
        
    except Exception as e:
        log.warning(f"⚠ Lỗi khi gọi API: {e}")
        return None


def generate_korean_identity() -> Dict[str, str]:
    """
    Generate Korean identity (try API first, fallback to random)
    
    Returns:
        Dict with name, email, phone
    """
    # Try API first
    identity = get_korean_identity_from_api()
    
    if identity:
        return identity
    
    # Fallback to random generation
    log.info("📝 Tạo thông tin Korean ngẫu nhiên...")
    
    korean_name = generate_korean_name()
    romanized_name = romanize_korean_name(korean_name)
    
    # Generate random email
    email_prefix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    email = f"{email_prefix}@gmail.com"
    
    # Generate random Korean phone (010-XXXX-XXXX format)
    phone = f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    
    identity = {
        "name": romanized_name,
        "email": email,
        "phone": phone
    }
    
    log.success(f"✓ Đã tạo thông tin: {identity['name']}")
    return identity
