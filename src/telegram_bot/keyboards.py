"""Keyboard layouts for Telegram bot"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 Đăng ký tài khoản", callback_data="register")],
        [InlineKeyboardButton("📋 Danh sách tài khoản", callback_data="accounts")],
        [InlineKeyboardButton("💳 Nâng cấp tài khoản", callback_data="upgrade")],
        [InlineKeyboardButton("⚙️ Cấu hình hệ thống", callback_data="config")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_accounts_list_keyboard():
    """Get keyboard for accounts list view"""
    keyboard = [
        [InlineKeyboardButton("💳 Nâng cấp tài khoản", callback_data="upgrade")],
        [InlineKeyboardButton("🏠 Quay lại menu chính", callback_data="back")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_config_keyboard():
    """Get keyboard for config view"""
    keyboard = [
        [InlineKeyboardButton("💳 Quản lý BIN", callback_data="config_bin")],
        [InlineKeyboardButton("🌐 Quản lý Proxy", callback_data="config_proxy")],
        [InlineKeyboardButton("🏠 Quay lại menu chính", callback_data="back")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Get simple back keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏠 Quay lại menu chính", callback_data="back")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_account_selection_keyboard(accounts: list):
    """Get account selection keyboard"""
    keyboard = []
    for i, acc in enumerate(accounts):
        email = acc.get('email', 'Unknown')
        keyboard.append([
            InlineKeyboardButton(
                f"{i+1}. {email}", 
                callback_data=f"select_account_{i}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🏠 Quay lại", callback_data="back"),
        InlineKeyboardButton("❓ Trợ giúp", callback_data="help")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_register_keyboard():
    """Get registration options keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("1 tài khoản", callback_data="register_1"),
            InlineKeyboardButton("5 tài khoản", callback_data="register_5")
        ],
        [
            InlineKeyboardButton("10 tài khoản", callback_data="register_10"),
            InlineKeyboardButton("Tùy chỉnh số lượng", callback_data="register_custom")
        ],
        [InlineKeyboardButton("🏠 Quay lại menu chính", callback_data="back")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Get confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Hủy", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_proxy_management_keyboard():
    """Get proxy management keyboard"""
    keyboard = [
        [InlineKeyboardButton("📋 Xem danh sách Proxy", callback_data="proxy_list")],
        [InlineKeyboardButton("➕ Thêm Proxy mới", callback_data="proxy_add")],
        [InlineKeyboardButton("✅ Kiểm tra Proxy", callback_data="proxy_check")],
        [InlineKeyboardButton("📊 Thống kê Proxy", callback_data="proxy_stats")],
        [InlineKeyboardButton("🗑️ Xóa Proxy", callback_data="proxy_delete_menu")],
        [InlineKeyboardButton("🏠 Quay lại cấu hình", callback_data="config")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_proxy_delete_keyboard():
    """Get proxy delete options keyboard"""
    keyboard = [
        [InlineKeyboardButton("🗑️ Xóa proxy inactive", callback_data="proxy_delete_inactive")],
        [InlineKeyboardButton("🗑️ Xóa proxy lỗi nhiều", callback_data="proxy_delete_failed")],
        [InlineKeyboardButton("⚠️ Xóa tất cả proxy", callback_data="proxy_delete_all_confirm")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="config_proxy")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bin_selection_keyboard(bins: list):
    """Get BIN selection keyboard"""
    keyboard = []
    
    # Show first 10 BINs
    for i, bin_num in enumerate(bins[:10], 1):
        keyboard.append([InlineKeyboardButton(f"BIN: {bin_num}", callback_data=f"select_bin_{bin_num}")])
    
    # Add "All BINs" option
    keyboard.append([InlineKeyboardButton("🎲 Thử tất cả BIN", callback_data="select_bin_all")])
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="upgrade")])
    
    return InlineKeyboardMarkup(keyboard)

def get_card_quantity_keyboard():
    """Get card quantity selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("1 thẻ", callback_data="card_qty_1"),
            InlineKeyboardButton("3 thẻ", callback_data="card_qty_3")
        ],
        [
            InlineKeyboardButton("5 thẻ", callback_data="card_qty_5"),
            InlineKeyboardButton("10 thẻ", callback_data="card_qty_10")
        ],
        [
            InlineKeyboardButton("Tùy chỉnh", callback_data="card_qty_custom")
        ],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="upgrade")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bin_management_keyboard():
    """Get BIN management keyboard"""
    keyboard = [
        [InlineKeyboardButton("📋 Xem danh sách BIN", callback_data="bin_list")],
        [InlineKeyboardButton("➕ Thêm BIN mới", callback_data="bin_add")],
        [InlineKeyboardButton("📊 Thống kê BIN", callback_data="bin_stats")],
        [InlineKeyboardButton("🏆 Top BIN tốt nhất", callback_data="bin_top")],
        [InlineKeyboardButton("🏠 Quay lại cấu hình", callback_data="config")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)
    """Get BIN management keyboard"""
    keyboard = [
        [InlineKeyboardButton("📋 Xem danh sách BIN", callback_data="bin_list")],
        [InlineKeyboardButton("➕ Thêm BIN mới", callback_data="bin_add")],
        [InlineKeyboardButton("📊 Thống kê BIN", callback_data="bin_stats")],
        [InlineKeyboardButton("🏆 Top BIN tốt nhất", callback_data="bin_top")],
        [InlineKeyboardButton("🏠 Quay lại cấu hình", callback_data="config")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)
