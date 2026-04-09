"""Message templates for Telegram bot"""

WELCOME_MESSAGE = """
🤖 Chào mừng đến với ChatGPT Auto Bot!

Bot này giúp bạn:
• Đăng ký tài khoản ChatGPT tự động
• Nâng cấp lên ChatGPT Plus/Team
• Quản lý nhiều tài khoản

Sử dụng /help để xem danh sách lệnh.
"""

HELP_MESSAGE = """
📋 Danh sách lệnh:

🔐 Quản lý tài khoản:
/register - Đăng ký tài khoản mới
/accounts - Xem danh sách tài khoản
/status - Kiểm tra trạng thái

💳 Thanh toán:
/upgrade - Nâng cấp tài khoản
/payment_status - Trạng thái thanh toán

⚙️ Cấu hình:
/config - Xem cấu hình hiện tại
/help - Hiển thị trợ giúp này
"""

def format_account_info(account: dict) -> str:
    """Format account information"""
    email = account.get('email', 'N/A')
    created = account.get('created_at', 'N/A')
    if created != 'N/A':
        created = created.split('T')[0]
    
    return f"""
📧 Email: `{email}`
📅 Tạo lúc: {created}
"""

def format_registration_result(result) -> str:
    """Format registration result"""
    if result.success:
        return f"""
✅ Đăng ký thành công!

📧 Email: `{result.email}`
🔑 Password: `{result.password}`
👤 Tên: {result.name}
📅 Ngày sinh: {result.birthdate}
"""
    else:
        return f"❌ Đăng ký thất bại: {result.error}"

def format_payment_result(result) -> str:
    """Format payment result"""
    if result.success:
        return f"""
✅ Thanh toán thành công!

💼 Workspace: {result.workspace_name}
🆔 Session: {result.checkout_session_id[:30]}...
💳 Payment Method: {result.payment_method_id[:30]}...
"""
    else:
        return f"❌ Thanh toán thất bại: {result.error}"
