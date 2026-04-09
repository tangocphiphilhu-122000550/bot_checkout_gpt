"""Card generator - Generate card numbers from BIN"""
import random
from typing import Optional, Tuple
from pathlib import Path
from .logger import log


def luhn_checksum(card_number: str) -> int:
    """Calculate Luhn checksum for card number"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10


def calculate_luhn(partial_card_number: str) -> str:
    """Calculate and append Luhn check digit"""
    check_digit = luhn_checksum(partial_card_number + '0')
    return str((10 - check_digit) % 10)


def generate_card_from_bin(bin_number: str) -> str:
    """
    Generate valid card number from BIN
    
    Args:
        bin_number: First 6-8 digits of card (BIN)
        
    Returns:
        Full 16-digit card number with valid Luhn checksum
    """
    # Ensure BIN is at least 6 digits
    if len(bin_number) < 6:
        raise ValueError("BIN must be at least 6 digits")
    
    # Generate random digits to make 15 digits total
    remaining_length = 15 - len(bin_number)
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(remaining_length)])
    
    # Combine BIN + random digits
    partial_card = bin_number + random_digits
    
    # Calculate and append Luhn check digit
    check_digit = calculate_luhn(partial_card)
    full_card = partial_card + check_digit
    
    return full_card


def generate_expiry() -> Tuple[str, str]:
    """
    Generate random expiry date (future date)
    
    Returns:
        Tuple of (month, year) as strings
    """
    # Random month between 01-12
    month = str(random.randint(1, 12)).zfill(2)
    
    # Random year between 2026-2030
    year = str(random.randint(2026, 2030))
    
    return month, year


def generate_cvv() -> str:
    """
    Generate random CVV (3 digits)
    
    Returns:
        3-digit CVV as string
    """
    return str(random.randint(100, 999))


def generate_full_card(bin_number: str) -> dict:
    """
    Generate full card details from BIN
    
    Args:
        bin_number: First 6-8 digits of card
        
    Returns:
        Dict with card_number, exp_month, exp_year, cvv
    """
    card_number = generate_card_from_bin(bin_number)
    exp_month, exp_year = generate_expiry()
    cvv = generate_cvv()
    
    return {
        "card_number": card_number,
        "exp_month": exp_month,
        "exp_year": exp_year,
        "cvv": cvv
    }


def save_bin(bin_number: str, bin_file: str = "card_bin.txt"):
    """Save BIN to file for reuse"""
    bin_path = Path(bin_file)
    with open(bin_path, 'w', encoding='utf-8') as f:
        f.write(bin_number)
    log.success(f"💾 Đã lưu BIN vào {bin_file}")


def load_bin(bin_file: str = "card_bin.txt") -> Optional[str]:
    """Load BIN from file"""
    bin_path = Path(bin_file)
    if bin_path.exists():
        with open(bin_path, 'r', encoding='utf-8') as f:
            bin_number = f.read().strip()
            if bin_number:
                log.info(f"📂 Đã tải BIN từ {bin_file}: {bin_number}")
                return bin_number
    return None


def load_all_bins(bin_file: str = "card_bin.txt") -> list:
    """
    Load tất cả BIN từ database, fallback to file
    
    Returns:
        List of BIN strings
    """
    bins = []
    
    # Try to load from database first
    try:
        from database.repository import CardBinRepository
        db_bins = CardBinRepository.get_all()
        bins = [b['bin_number'] for b in db_bins]
        
        if bins:
            log.info(f"📂 Đã tải {len(bins)} BIN từ database")
            return bins
    except Exception as e:
        log.warning(f"⚠️ Could not load from database: {e}")
    
    # Fallback to file
    bin_path = Path(bin_file)
    if not bin_path.exists():
        log.warning(f"⚠️ No BIN file found: {bin_file}")
        return []
    
    with open(bin_path, 'r', encoding='utf-8') as f:
        for line in f:
            bin_number = line.strip()
            # Validate BIN
            if bin_number and bin_number.isdigit() and len(bin_number) >= 6:
                bins.append(bin_number)
    
    if bins:
        log.info(f"📂 Đã tải {len(bins)} BIN từ file")
    
    return bins


def get_or_input_bin(bin_file: str = "card_bin.txt") -> str:
    """Get BIN from file or ask user to input"""
    # Try to load from file
    bin_number = load_bin(bin_file)
    
    if bin_number:
        use_saved = input(f"Sử dụng BIN đã lưu ({bin_number})? (y/n): ").strip().lower()
        if use_saved == 'y':
            return bin_number
    
    # Ask user for new BIN
    bin_number = input("Nhập BIN của thẻ (6-8 số đầu): ").strip()
    
    # Validate BIN
    if not bin_number.isdigit() or len(bin_number) < 6:
        raise ValueError("BIN phải là số và có ít nhất 6 chữ số")
    
    # Save for next time
    save_bin(bin_number, bin_file)
    
    return bin_number
