"""Điểm khởi đầu chính cho ChatGPT Auto Bot"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from register.register_bot import ChatGPTRegistrationBot, RegistrationResult
from payment.payment_bot import ChatGPTPaymentBot, PaymentConfig, PaymentResult
from utils.token_helper import get_access_token
from utils.card_generator import get_or_input_bin, generate_full_card, load_all_bins
from utils.korean_identity import generate_korean_identity
from utils.logger import log
from utils.config import settings

# Database imports
from database.connection import init_database
from database.repository import AccountRepository, PaymentRepository, CardBinRepository


def save_account(result: RegistrationResult):
    """Lưu tài khoản vào database"""
    
    if not result.success:
        log.warning("⚠ Đăng ký tài khoản thất bại, không lưu")
        return
    
    try:
        AccountRepository.create(
            email=result.email,
            password=result.password,
            name=result.name,
            birthdate=result.birthdate,
            cookies=result.cookies
        )
    except Exception as e:
        log.error(f"❌ Lỗi lưu tài khoản vào database: {e}")
        # Fallback to JSON file
        save_account_to_json(result)

def save_account_to_json(result: RegistrationResult, output_file: str = "accounts.json"):
    """Fallback: Lưu tài khoản vào file JSON"""
    output_path = Path(output_file)
    accounts = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        except:
            accounts = []
    accounts.append(result.to_dict())
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    log.success(f"💾 Đã lưu tài khoản vào {output_file}")


def register_single_account(password: str = None, save: bool = True):
    """Đăng ký một tài khoản ChatGPT"""
    
    with ChatGPTRegistrationBot(password=password) as bot:
        result = bot.register()
        
        if result.success:
            log.success("✅ Đăng ký thành công!")
            
            if save:
                save_account(result)
            
            return result
        else:
            log.error(f"❌ Đăng ký thất bại: {result.error}")
            return result


def register_multiple_accounts(count: int, password: str = None, save: bool = True):
    """Đăng ký nhiều tài khoản ChatGPT"""
    
    log.info(f"🔄 Bắt đầu đăng ký hàng loạt: {count} tài khoản")
    log.info("")
    
    results = []
    success_count = 0
    
    for i in range(1, count + 1):
        log.info(f"📝 Đang đăng ký tài khoản {i}/{count}")
        log.info("-" * 60)
        
        result = register_single_account(password=password, save=save)
        results.append(result)
        
        if result.success:
            success_count += 1
        
        log.info("")
        log.info("=" * 60)
        log.info("")
    
    # Tổng kết
    log.info("📊 TỔNG KẾT ĐĂNG KÝ HÀNG LOẠT")
    log.info("=" * 60)
    log.info(f"Tổng số: {count}")
    log.info(f"Thành công: {success_count}")
    log.info(f"Thất bại: {count - success_count}")
    log.info(f"Tỷ lệ thành công: {success_count / count * 100:.1f}%")
    log.info("=" * 60)
    
    return results


def process_payment_for_account(account_data: dict, max_retries: int = None):
    """Xử lý thanh toán cho tài khoản đã đăng ký với auto-retry"""
    
    # Dùng config mặc định nếu không truyền vào
    if max_retries is None:
        max_retries = settings.max_payment_retries
    
    log.info("=" * 60)
    log.info("💳 THIẾT LẬP THANH TOÁN")
    log.info("=" * 60)
    
    # Lấy access token
    cookies = account_data.get("cookies", {})
    access_token = get_access_token(cookies)
    
    if not access_token:
        log.error("❌ Không thể lấy access token")
        return None
    
    log.info("")
    
    # ============================================================
    # HỎI TẤT CẢ CÂU HỎI Ở ĐẦU
    # ============================================================
    
    # 1. Workspace info
    workspace_name = input("Tên workspace: ").strip()
    country = input("Mã quốc gia (mặc định: KR): ").strip() or "KR"
    
    # 2. BIN selection
    log.info("")
    log.info("=" * 60)
    log.info("💳 CHỌN BIN")
    log.info("=" * 60)
    
    all_bins = load_all_bins()
    
    if not all_bins:
        log.warning("⚠ Không tìm thấy BIN trong card_bin.txt")
        try:
            bin_number = get_or_input_bin()
            all_bins = [bin_number]
        except ValueError as e:
            log.error(f"❌ {e}")
            return None
    else:
        log.info("")
        use_all = input(f"Tìm thấy {len(all_bins)} BIN. Dùng tất cả? (y/n): ").strip().lower()
        
        if use_all != 'y':
            choice = int(input(f"Chọn BIN (1-{len(all_bins)}): ").strip())
            if 1 <= choice <= len(all_bins):
                all_bins = [all_bins[choice - 1]]
            else:
                log.error("❌ Lựa chọn không hợp lệ")
                return None
    
    # 3. Retry config
    log.info("")
    cards_per_bin_input = input(f"Số thẻ muốn thử cho MỖI BIN (mặc định: {max_retries}): ").strip()
    if cards_per_bin_input:
        try:
            cards_per_bin = int(cards_per_bin_input)
        except:
            log.warning(f"⚠ Giá trị không hợp lệ, dùng mặc định: {max_retries}")
            cards_per_bin = max_retries
    else:
        cards_per_bin = max_retries
    
    # ============================================================
    # HIỂN THỊ CHIẾN LƯỢC
    # ============================================================
    
    log.info("")
    log.info("=" * 60)
    log.info("📊 CHIẾN LƯỢC RETRY")
    log.info("=" * 60)
    log.info(f"   Workspace: {workspace_name}")
    log.info(f"   Country: {country}")
    log.info(f"   Số BIN: {len(all_bins)}")
    log.info(f"   Thẻ/BIN: {cards_per_bin}")
    log.info(f"   Tổng thẻ tối đa: {len(all_bins) * cards_per_bin}")
    log.info("=" * 60)
    
    # Confirm
    log.info("")
    confirm = input("Bắt đầu? (y/n): ").strip().lower()
    if confirm != 'y':
        log.info("❌ Đã hủy")
        return None
    
    # ============================================================
    # TẠO KOREAN IDENTITY (1 LẦN)
    # ============================================================
    
    log.info("")
    log.info("=" * 60)
    log.info("🇰🇷 TẠO THÔNG TIN KOREAN")
    log.info("=" * 60)
    
    korean_identity = generate_korean_identity()
    billing_email = account_data.get("email", korean_identity['email'])
    
    log.success(f"✓ Tên: {korean_identity['name']}")
    log.success(f"✓ Email: {billing_email} (từ tài khoản)")
    log.success(f"✓ SĐT: {korean_identity['phone']}")
    
    # ============================================================
    # BẮT ĐẦU PAYMENT FLOW
    # ============================================================
    
    log.info("")
    log.info("=" * 60)
    log.info(f"🔄 BẮT ĐẦU MULTI-BIN RETRY")
    log.info("=" * 60)
    log.info("")
    
    # Tạo checkout session 1 LẦN DUY NHẤT (reuse cho tất cả retry)
    log.info("🔧 Tạo checkout session...")
    with ChatGPTPaymentBot(access_token, cookies) as payment_bot:
        # Get countries
        from payment.payment_api import ChatGPTPaymentAPI
        payment_api = ChatGPTPaymentAPI(access_token, cookies)
        
        countries = payment_api.get_countries()
        if countries and country not in countries:
            log.warning(f"⚠ Country {country} not in available list")
        
        # Create checkout session
        checkout_data = payment_api.create_checkout_session(
            workspace_name=workspace_name,
            country=country,
            currency="USD",
            seat_quantity=5,
            price_interval="month"
        )
        
        if not checkout_data:
            log.error("❌ Không thể tạo checkout session")
            return None
        
        checkout_session_id = checkout_data.get("checkout_session_id")
        publishable_key = checkout_data.get("publishable_key")
        
        if not checkout_session_id or not publishable_key:
            log.error("❌ Thiếu checkout session ID hoặc publishable key")
            return None
        
        log.success(f"✓ Checkout session created: {checkout_session_id[:30]}...")
        
        # Convert to Stripe URL (1 lần duy nhất)
        from payment.stripe_converter import convert_to_stripe_url
        stripe_url = convert_to_stripe_url(checkout_session_id)
        log.success(f"✓ Stripe URL: {stripe_url[:60]}...")
        
        # Get expected amount
        from payment.stripe_api import StripePaymentAPI
        stripe_api = StripePaymentAPI(publishable_key, country_code=country)
        
        log.info("💰 Fetching expected amount from checkout session...")
        session_info = stripe_api.get_checkout_session_info(checkout_session_id)
        
        if session_info:
            invoice = session_info.get("invoice", {})
            expected_amount = invoice.get("total", 0)
            log.info(f"   ✅ Expected amount: {expected_amount}")
        else:
            expected_amount = 0
            log.warning("   Could not fetch session info, using expected_amount=0")
        
        log.info("")
        log.info("=" * 60)
        log.info("🔄 MULTI-BIN RETRY LOOP")
        log.info("=" * 60)
        log.info("")
    
    # Loop qua tất cả BIN
    total_attempts = 0
    for bin_index, bin_number in enumerate(all_bins, 1):
        log.info("=" * 60)
        log.info(f"💳 BIN {bin_index}/{len(all_bins)}: {bin_number}")
        log.info("=" * 60)
        log.info("")
        
        # Thử N thẻ cho BIN này
        for card_attempt in range(1, cards_per_bin + 1):
            total_attempts += 1
            
            log.info("=" * 60)
            log.info(f"🎯 LẦN THỬ {total_attempts} (BIN {bin_index}/{len(all_bins)}, Thẻ {card_attempt}/{cards_per_bin})")
            log.info("=" * 60)
            
            # Tạo thông tin thẻ mới cho mỗi lần thử
            log.info("🎲 Đang tạo thông tin thẻ từ BIN...")
            card_info = generate_full_card(bin_number)
            
            log.success(f"✓ Số thẻ: {card_info['card_number']}")
            log.success(f"✓ Hạn: {card_info['exp_month']}/{card_info['exp_year']}")
            log.success(f"✓ CVV: {card_info['cvv']}")
            log.info("")
            
            # Tạo cấu hình thanh toán
            config = PaymentConfig(
                workspace_name=workspace_name,
                card_number=card_info['card_number'],
                exp_month=card_info['exp_month'],
                exp_year=card_info['exp_year'],
                cvc=card_info['cvv'],
                billing_name=korean_identity['name'],
                billing_email=billing_email,
                country=country
            )
            
            # Thử thanh toán với thẻ này (KHÔNG TẠO SESSION MỚI)
            with ChatGPTPaymentBot(access_token, cookies) as payment_bot:
                result = payment_bot.try_payment_with_card(
                    config=config,
                    checkout_session_id=checkout_session_id,
                    publishable_key=publishable_key,
                    expected_amount=expected_amount,
                    stripe_url=stripe_url  # Pass URL đã convert sẵn
                )
            
            if result.success:
                log.info("")
                log.info("=" * 60)
                log.success(f"🎉 THANH TOÁN THÀNH CÔNG SAU {total_attempts} LẦN THỬ!")
                log.info("=" * 60)
                log.info(f"💳 BIN thành công: {bin_number}")
                log.info(f"💳 Thẻ thành công: {card_info['card_number']}")
                log.info(f"💼 Workspace: {workspace_name}")
                log.info("=" * 60)
                return result
            else:
                # Check if session expired/canceled
                if result.error and "setup_intent_unexpected_state" in result.error:
                    log.warning("")
                    log.warning("=" * 60)
                    log.warning("⚠️ SESSION ĐÃ HẾT HẠN HOẶC BỊ CANCEL")
                    log.warning("=" * 60)
                    log.warning("🔄 Đang tạo session mới...")
                    log.warning("")
                    
                    # Tạo session mới
                    from payment.payment_api import ChatGPTPaymentAPI
                    payment_api = ChatGPTPaymentAPI(access_token, cookies)
                    
                    checkout_data = payment_api.create_checkout_session(
                        workspace_name=workspace_name,
                        country=country,
                        currency="USD",
                        seat_quantity=5,
                        price_interval="month"
                    )
                    
                    if not checkout_data:
                        log.error("❌ Không thể tạo session mới")
                        return result
                    
                    checkout_session_id = checkout_data.get("checkout_session_id")
                    publishable_key = checkout_data.get("publishable_key")
                    
                    if not checkout_session_id or not publishable_key:
                        log.error("❌ Thiếu checkout session ID hoặc publishable key")
                        return result
                    
                    log.success(f"✓ Session mới: {checkout_session_id[:30]}...")
                    
                    # Convert URL mới
                    from payment.stripe_converter import convert_to_stripe_url
                    stripe_url = convert_to_stripe_url(checkout_session_id)
                    
                    # Get expected amount mới
                    from payment.stripe_api import StripePaymentAPI
                    stripe_api = StripePaymentAPI(publishable_key, country_code=country)
                    session_info = stripe_api.get_checkout_session_info(checkout_session_id)
                    
                    if session_info:
                        invoice = session_info.get("invoice", {})
                        expected_amount = invoice.get("total", 0)
                        log.info(f"✓ Expected amount: {expected_amount}")
                    else:
                        expected_amount = 0
                    
                    log.warning("🔄 Tiếp tục với session mới...")
                    log.info("")
                    
                    # Retry với session mới (không tăng counter)
                    with ChatGPTPaymentBot(access_token, cookies) as payment_bot:
                        result = payment_bot.try_payment_with_card(
                            config=config,
                            checkout_session_id=checkout_session_id,
                            publishable_key=publishable_key,
                            expected_amount=expected_amount,
                            stripe_url=stripe_url
                        )
                    
                    # Check result sau khi retry với session mới
                    if result.success:
                        log.info("")
                        log.info("=" * 60)
                        log.success(f"🎉 THANH TOÁN THÀNH CÔNG SAU {total_attempts} LẦN THỬ!")
                        log.info("=" * 60)
                        log.info(f"💳 BIN thành công: {bin_number}")
                        log.info(f"💳 Thẻ thành công: {card_info['card_number']}")
                        log.info(f"💼 Workspace: {workspace_name}")
                        log.info("=" * 60)
                        return result
                
                log.error(f"❌ Lần thử {total_attempts} thất bại: {result.error}")
                
                # Kiểm tra nếu còn thẻ để thử trong BIN này
                if card_attempt < cards_per_bin:
                    log.warning(f"🔄 Thử thẻ khác từ BIN {bin_number}... (Còn {cards_per_bin - card_attempt} thẻ)")
                    log.info("")
                elif bin_index < len(all_bins):
                    log.warning(f"🔄 BIN {bin_number} hết thẻ. Chuyển sang BIN tiếp theo...")
                    log.info("")
                    break  # Chuyển sang BIN tiếp theo
                else:
                    # Hết tất cả BIN và thẻ
                    log.error("")
                    log.error("=" * 60)
                    log.error(f"❌ ĐÃ THỬ {total_attempts} LẦN ({len(all_bins)} BIN x {cards_per_bin} thẻ) NHƯNG VẪN THẤT BẠI")
                    log.error("=" * 60)
                    log.error("💡 Khuyến nghị:")
                    log.error("   1. Thêm BIN khác vào card_bin.txt")
                    log.error("   2. Kiểm tra proxy (phải là Korea residential)")
                    log.error("   3. Đổi Korean identity")
                    log.error("   4. Chờ một lúc rồi thử lại")
                    log.error("=" * 60)
                    return result
    
    return None


def register_and_pay():
    """Đăng ký tài khoản và thanh toán ngay"""
    
    # Bước 1: Đăng ký tài khoản
    password = input("Nhập mật khẩu (hoặc Enter để dùng mặc định): ").strip() or None
    result = register_single_account(password=password, save=True)
    
    if not result.success:
        log.error("❌ Đăng ký thất bại, không thể tiếp tục thanh toán")
        return
    
    log.info("")
    log.info("✅ Đăng ký hoàn tất!")
    log.info("")
    
    # Bước 2: Hỏi có muốn thanh toán không
    pay_now = input("Bạn có muốn đăng ký workspace ngay không? (y/n): ").strip().lower()
    
    if pay_now == 'y':
        account_data = result.to_dict()
        process_payment_for_account(account_data)
    else:
        log.info("💡 Bạn có thể thanh toán sau bằng tùy chọn 4")


def pay_for_existing_account():
    """Xử lý thanh toán cho tài khoản đã có"""
    
    # Tải danh sách tài khoản từ database
    try:
        accounts = AccountRepository.get_all()
        accounts_list = [acc.to_dict() for acc in accounts]
    except Exception as e:
        log.error(f"❌ Lỗi load từ database: {e}")
        # Fallback to JSON
        accounts_file = Path("accounts.json")
        if not accounts_file.exists():
            log.error("❌ Không tìm thấy tài khoản. Vui lòng đăng ký tài khoản trước.")
            return
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts_list = json.load(f)
    
    if not accounts_list:
        log.error("❌ Không tìm thấy tài khoản. Vui lòng đăng ký tài khoản trước.")
        return
    
    # Hiển thị danh sách tài khoản
    print("\n📋 Danh sách tài khoản:")
    for i, acc in enumerate(accounts_list, 1):
        email = acc.get("email", "Không rõ")
        created = acc.get("created_at", "Không rõ")
        print(f"{i}. {email} (tạo lúc: {created})")
    
    print()
    choice = int(input("Chọn số thứ tự tài khoản: ").strip())
    
    if choice < 1 or choice > len(accounts_list):
        log.error("❌ Số thứ tự không hợp lệ")
        return
    
    account_data = accounts_list[choice - 1]
    result = process_payment_for_account(account_data)
    
    # Save payment result to database
    if result:
        try:
            PaymentRepository.create(
                account_email=account_data.get('email'),
                workspace_name=result.workspace_name,
                checkout_session_id=result.checkout_session_id,
                payment_method_id=result.payment_method_id,
                payment_status=result.payment_status,
                success=result.success,
                error=result.error
            )
        except Exception as e:
            log.warning(f"⚠ Không lưu được payment vào database: {e}")


def main():
    """Hàm chính"""
    
    # Kiểm tra file .env
    if not Path(".env").exists():
        log.error("❌ Không tìm thấy file .env!")
        log.info("📝 Vui lòng tạo file .env từ .env.example")
        log.info("   cp .env.example .env")
        log.info("   Sau đó chỉnh sửa .env với API keys của bạn")
        sys.exit(1)
    
    # Initialize database
    try:
        init_database()
        log.success("✅ Database connected")
    except Exception as e:
        log.warning(f"⚠ Database connection failed: {e}")
        log.warning("⚠ Sẽ sử dụng file JSON làm fallback")
    
    # Giao diện CLI đơn giản
    print("\n" + "=" * 60)
    print("🤖 ChatGPT Auto Bot - Đăng Ký & Thanh Toán")
    print("=" * 60)
    print("\nTùy chọn:")
    print("1. Đăng ký 1 tài khoản")
    print("2. Đăng ký nhiều tài khoản")
    print("3. Đăng ký + Đăng ký workspace")
    print("4. Đăng ký workspace cho tài khoản có sẵn")
    print("5. Thoát")
    print()
    
    choice = input("Chọn tùy chọn (1-5): ").strip()
    
    if choice == "1":
        password = input("Nhập mật khẩu (hoặc Enter để dùng mặc định): ").strip() or None
        register_single_account(password=password)
        
    elif choice == "2":
        count = int(input("Số lượng tài khoản: "))
        password = input("Nhập mật khẩu (hoặc Enter để dùng mặc định): ").strip() or None
        register_multiple_accounts(count=count, password=password)
        
    elif choice == "3":
        register_and_pay()
        
    elif choice == "4":
        pay_for_existing_account()
        
    elif choice == "5":
        log.info("👋 Tạm biệt!")
        sys.exit(0)
        
    else:
        log.error("❌ Lựa chọn không hợp lệ")
        sys.exit(1)


if __name__ == "__main__":
    main()
