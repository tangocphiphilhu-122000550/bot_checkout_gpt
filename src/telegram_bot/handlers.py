"""Command handlers for Telegram bot"""
import json
import sys
from pathlib import Path

# Add parent directory to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import telegram library
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import local modules
from telegram_bot.messages import (
    WELCOME_MESSAGE, HELP_MESSAGE,
    format_account_info, format_registration_result, format_payment_result
)
from telegram_bot.keyboards import (
    get_main_menu_keyboard, get_account_selection_keyboard,
    get_register_keyboard, get_confirmation_keyboard,
    get_accounts_list_keyboard, get_config_keyboard,
    get_back_keyboard, get_proxy_management_keyboard,
    get_bin_management_keyboard, get_proxy_delete_keyboard,
    get_bin_selection_keyboard, get_card_quantity_keyboard,
    get_bin_delete_keyboard, get_bin_list_delete_keyboard
)
from register.register_bot import ChatGPTRegistrationBot
from payment.payment_bot import ChatGPTPaymentBot, PaymentConfig
from utils.card_generator import load_all_bins, generate_full_card
from utils.korean_identity import generate_korean_identity
from utils.logger import log

# Database imports
from database.repository import AccountRepository, PaymentRepository, CardBinRepository, LogRepository


ACCOUNTS_FILE = Path("accounts.json")


def load_accounts():
    """Load accounts from database"""
    try:
        accounts = AccountRepository.get_all()
        log.info(f"📊 Loaded {len(accounts)} accounts from database")
        return accounts
    except Exception as e:
        log.error(f"❌ Failed to load from database: {e}")
        # Fallback to JSON file
        if not ACCOUNTS_FILE.exists():
            return []
        try:
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                log.info(f"📊 Loaded {len(data)} accounts from JSON file")
                return data
        except Exception as e2:
            log.error(f"❌ Failed to load from JSON: {e2}")
            return []


def save_account(account_dict: dict):
    """Save account to database"""
    try:
        AccountRepository.create(
            email=account_dict['email'],
            password=account_dict['password'],
            name=account_dict.get('name'),
            birthdate=account_dict.get('birthdate'),
            cookies=account_dict.get('cookies')
        )
        log.success(f"✅ Account saved to database: {account_dict['email']}")
    except Exception as e:
        log.error(f"❌ Failed to save to database: {e}")
        # Fallback to JSON file
        accounts = load_accounts()
        accounts.append(account_dict)
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        log.info(f"💾 Account saved to JSON file: {account_dict['email']}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        HELP_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command"""
    await update.message.reply_text(
        "Chọn số lượng tài khoản muốn đăng ký:",
        reply_markup=get_register_keyboard()
    )


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /accounts command"""
    accounts = load_accounts()
    
    if not accounts:
        await update.message.reply_text(
            "Chưa có tài khoản nào. Dùng /register để tạo mới.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    message = f"📋 Danh sách tài khoản ({len(accounts)}):\n"
    for i, acc in enumerate(accounts, 1):
        email = acc.get('email', 'N/A')
        created = acc.get('created_at', 'N/A')
        if created != 'N/A':
            created = created.split('T')[0]
        message += f"\n{i}. {email}\n   📅 {created}\n"
    
    await update.message.reply_text(
        message,
        reply_markup=get_accounts_list_keyboard()
    )


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upgrade command"""
    accounts = load_accounts()
    
    if not accounts:
        await update.message.reply_text("Chưa có tài khoản. Dùng /register trước.")
        return
    
    await update.message.reply_text(
        "Chọn tài khoản muốn nâng cấp:",
        reply_markup=get_account_selection_keyboard(accounts)
    )


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /config command"""
    bins = load_all_bins()
    
    try:
        from database.repository import ProxyRepository
        proxy_count = ProxyRepository.count(active_only=True)
    except:
        proxy_count = 0
    
    config_text = f"""
⚙️ Cấu hình hiện tại:

💳 BIN: {len(bins)} BIN
🌐 Proxy: {proxy_count} proxy active
📧 TempMail: Đã cấu hình
🔐 Password: Đã cấu hình
"""
    await update.message.reply_text(
        config_text,
        reply_markup=get_config_keyboard()
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    accounts = load_accounts()
    bins = load_all_bins()
    
    # Get log stats
    try:
        error_count = LogRepository.count_by_level('ERROR')
        warning_count = LogRepository.count_by_level('WARNING')
        log_status = f"❌ Errors: {error_count} | ⚠️ Warnings: {warning_count}"
    except:
        log_status = "📊 Logs: N/A"
    
    status_text = f"""
📊 Trạng thái hệ thống:

✅ Bot: Hoạt động
📝 Tài khoản: {len(accounts)}
💳 BIN: {len(bins)}
{log_status}
"""
    await update.message.reply_text(
        status_text,
        reply_markup=get_main_menu_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Main menu callbacks
    if data == "register":
        await query.edit_message_text(
            "Chọn số lượng tài khoản muốn đăng ký:",
            reply_markup=get_register_keyboard()
        )
    
    elif data == "accounts":
        accounts = load_accounts()
        if not accounts:
            await query.edit_message_text(
                "Chưa có tài khoản nào.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            message = f"📋 Danh sách tài khoản ({len(accounts)}):\n"
            for i, acc in enumerate(accounts, 1):
                email = acc.get('email', 'N/A')
                message += f"\n{i}. {email}"
            await query.edit_message_text(
                message,
                reply_markup=get_accounts_list_keyboard()
            )
    
    elif data == "upgrade":
        accounts = load_accounts()
        if not accounts:
            await query.edit_message_text(
                "Chưa có tài khoản.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                "Chọn tài khoản muốn nâng cấp:",
                reply_markup=get_account_selection_keyboard(accounts)
            )
    
    elif data == "config":
        bins = load_all_bins()
        try:
            from database.repository import ProxyRepository
            proxy_count = ProxyRepository.count(active_only=True)
        except:
            proxy_count = 0
        
        config_text = f"""
⚙️ Cấu hình:

💳 BIN: {len(bins)}
🌐 Proxy: {proxy_count} active
📧 TempMail: OK
🔐 Password: OK
"""
        await query.edit_message_text(
            config_text,
            reply_markup=get_config_keyboard()
        )
    
    # Config submenu
    elif data == "config_bin":
        bins = load_all_bins()
        try:
            from database.repository import CardBinRepository
            db_bins = CardBinRepository.get_all()
            bin_text = f"💳 Quản lý BIN\n\n"
            bin_text += f"📁 File: {len(bins)} BIN\n"
            bin_text += f"🗄️ Database: {len(db_bins)} BIN\n"
        except:
            bin_text = f"💳 Quản lý BIN\n\n📁 File: {len(bins)} BIN\n"
        
        await query.edit_message_text(
            bin_text,
            reply_markup=get_bin_management_keyboard()
        )
    
    elif data == "config_proxy":
        try:
            from database.repository import ProxyRepository
            proxies = ProxyRepository.get_all(active_only=True)
            proxy_text = f"🌐 Quản lý Proxy\n\n"
            proxy_text += f"✅ Active: {len(proxies)}\n"
            
            # Count by country
            countries = {}
            for p in proxies:
                country = p.get('country') or 'Unknown'
                countries[country] = countries.get(country, 0) + 1
            
            if countries:
                proxy_text += f"\n📍 Theo quốc gia:\n"
                for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
                    proxy_text += f"   {country}: {count}\n"
        except Exception as e:
            proxy_text = f"🌐 Quản lý Proxy\n\n⚠️ Chưa có proxy trong database"
        
        await query.edit_message_text(
            proxy_text,
            reply_markup=get_proxy_management_keyboard()
        )
    
    # Proxy management
    elif data == "proxy_list":
        try:
            from database.repository import ProxyRepository
            proxies = ProxyRepository.get_all(active_only=True)
            
            if not proxies:
                proxy_text = "🌐 Danh sách Proxy\n\n⚠️ Chưa có proxy"
            else:
                proxy_text = f"🌐 Danh sách Proxy ({len(proxies)}):\n\n"
                for i, p in enumerate(proxies[:10], 1):  # Show first 10
                    country = p.get('country') or '??'
                    success_rate = p.get('success_rate', 0)
                    proxy_url = p.get('proxy_url', '')
                    response_time = p.get('response_time') or 0
                    proxy_text += f"{i}. [{country}] {proxy_url[:30]}...\n"
                    proxy_text += f"   ✅ {success_rate:.1f}% | ⚡ {response_time}ms\n"
                
                if len(proxies) > 10:
                    proxy_text += f"\n... và {len(proxies) - 10} proxy khác"
        except Exception as e:
            proxy_text = f"❌ Lỗi: {str(e)}"
        
        await query.edit_message_text(
            proxy_text,
            reply_markup=get_proxy_management_keyboard()
        )
    
    elif data == "proxy_add":
        await query.edit_message_text(
            """
➕ Thêm Proxy

Chọn chế độ:
• Đơn lẻ: Gửi 1 message với nhiều proxy
• Hàng loạt: Gửi nhiều message, bot sẽ thu thập tất cả

Gửi "batch" để bật chế độ hàng loạt
Hoặc gửi proxy trực tiếp theo format:
user:pass@host:port

Ví dụ:
user1:pass1@proxy1.com:8080
user2:pass2@proxy2.com:8080

Hệ thống tự động thêm http://
Gửi /cancel để hủy
"""
        )
        context.user_data['waiting_for'] = 'proxy_url'
    
    elif data == "proxy_check":
        await query.edit_message_text(
            "✅ Đang kiểm tra proxy...\n\nChức năng này đang được phát triển.",
            reply_markup=get_proxy_management_keyboard()
        )
    
    elif data == "proxy_stats":
        try:
            from database.repository import ProxyRepository
            total = ProxyRepository.count()
            active = ProxyRepository.count(active_only=True)
            
            stats_text = f"""
📊 Thống kê Proxy

📦 Tổng: {total}
✅ Active: {active}
❌ Inactive: {total - active}
"""
        except Exception as e:
            stats_text = f"❌ Lỗi: {str(e)}"
        
        await query.edit_message_text(
            stats_text,
            reply_markup=get_proxy_management_keyboard()
        )
    
    elif data == "proxy_delete_menu":
        await query.edit_message_text(
            """
🗑️ Xóa Proxy

Chọn loại proxy muốn xóa:

• Inactive: Proxy đã bị đánh dấu không hoạt động
• Lỗi nhiều: Proxy có tỷ lệ lỗi >= 70%
• Tất cả: Xóa toàn bộ proxy (cẩn thận!)
""",
            reply_markup=get_proxy_delete_keyboard()
        )
    
    elif data == "proxy_delete_inactive":
        try:
            from database.repository import ProxyRepository
            count = ProxyRepository.delete_inactive()
            
            await query.edit_message_text(
                f"✅ Đã xóa {count} proxy inactive!",
                reply_markup=get_proxy_management_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lỗi: {str(e)}",
                reply_markup=get_proxy_management_keyboard()
            )
    
    elif data == "proxy_delete_failed":
        try:
            from database.repository import ProxyRepository
            count = ProxyRepository.delete_failed(min_fail_rate=0.7)
            
            await query.edit_message_text(
                f"✅ Đã xóa {count} proxy lỗi nhiều (>= 70%)!",
                reply_markup=get_proxy_management_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lỗi: {str(e)}",
                reply_markup=get_proxy_management_keyboard()
            )
    
    elif data == "proxy_delete_all_confirm":
        # Show confirmation for delete all
        keyboard = [
            [InlineKeyboardButton("⚠️ XÁC NHẬN XÓA TẤT CẢ", callback_data="proxy_delete_all_yes")],
            [InlineKeyboardButton("❌ Hủy", callback_data="proxy_delete_menu")]
        ]
        await query.edit_message_text(
            """
⚠️ CẢNH BÁO!

Bạn có chắc muốn xóa TẤT CẢ proxy?
Hành động này KHÔNG THỂ hoàn tác!
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "proxy_delete_all_yes":
        try:
            from database.repository import ProxyRepository
            count = ProxyRepository.delete_all()
            
            await query.edit_message_text(
                f"✅ Đã xóa tất cả {count} proxy!",
                reply_markup=get_proxy_management_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lỗi: {str(e)}",
                reply_markup=get_proxy_management_keyboard()
            )
    
    elif data == "bin_list":
        bins = load_all_bins()
        if not bins:
            bin_text = "💳 Danh sách BIN\n\n⚠️ Chưa có BIN"
        else:
            bin_text = f"💳 Danh sách BIN ({len(bins)}):\n\n"
            for i, bin_num in enumerate(bins[:10], 1):
                bin_text += f"{i}. {bin_num}\n"
            
            if len(bins) > 10:
                bin_text += f"\n... và {len(bins) - 10} BIN khác"
        
        await query.edit_message_text(
            bin_text,
            reply_markup=get_bin_management_keyboard()
        )
    
    elif data == "bin_add":
        await query.edit_message_text(
            """
➕ Thêm BIN

Gửi BIN (6-8 số đầu của thẻ):

📝 Có thể gửi nhiều BIN cùng lúc, mỗi dòng 1 BIN:
Ví dụ:
123456
234567
345678

Hoặc gửi /cancel để hủy
"""
        )
        context.user_data['waiting_for'] = 'bin_number'
    
    elif data == "bin_stats":
        try:
            from database.repository import CardBinRepository
            bins = CardBinRepository.get_all()
            
            if not bins:
                stats_text = "📊 Thống kê BIN\n\n⚠️ Chưa có dữ liệu"
            else:
                total_success = sum(b.get('success_count', 0) for b in bins)
                total_fail = sum(b.get('fail_count', 0) for b in bins)
                
                stats_text = f"""
📊 Thống kê BIN

💳 Tổng BIN: {len(bins)}
✅ Thành công: {total_success}
❌ Thất bại: {total_fail}
"""
        except Exception as e:
            stats_text = f"❌ Lỗi: {str(e)}"
        
        await query.edit_message_text(
            stats_text,
            reply_markup=get_bin_management_keyboard()
        )
    
    elif data == "bin_top":
        try:
            from database.repository import CardBinRepository
            bins = CardBinRepository.get_best_bins(limit=10)
            
            if not bins:
                top_text = "🏆 Top BIN\n\n⚠️ Chưa có dữ liệu"
            else:
                top_text = f"🏆 Top {len(bins)} BIN tốt nhất:\n\n"
                for i, b in enumerate(bins, 1):
                    bin_number = b.get('bin_number')
                    success_count = b.get('success_count', 0)
                    fail_count = b.get('fail_count', 0)
                    total = success_count + fail_count
                    rate = (success_count / total * 100) if total > 0 else 0
                    top_text += f"{i}. {bin_number}\n"
                    top_text += f"   ✅ {rate:.1f}% ({success_count}/{total})\n"
        except Exception as e:
            top_text = f"❌ Lỗi: {str(e)}"
        
        await query.edit_message_text(
            top_text,
            reply_markup=get_bin_management_keyboard()
        )
    
    elif data == "bin_delete_menu":
        await query.edit_message_text(
            """
🗑️ Xóa BIN

Chọn loại xóa:

• Xóa BIN cụ thể: Chọn BIN muốn xóa
• Xóa tất cả: Xóa toàn bộ BIN (cẩn thận!)
""",
            reply_markup=get_bin_delete_keyboard()
        )
    
    elif data == "bin_delete_select":
        bins = load_all_bins()
        
        if not bins:
            await query.edit_message_text(
                "⚠️ Không có BIN nào để xóa!",
                reply_markup=get_bin_management_keyboard()
            )
        else:
            await query.edit_message_text(
                f"🗑️ Chọn BIN muốn xóa:\n\n📊 Tổng: {len(bins)} BIN",
                reply_markup=get_bin_list_delete_keyboard(bins)
            )
    
    elif data.startswith("delete_bin_"):
        bin_to_delete = data.split("_", 2)[2]
        
        try:
            from database.repository import CardBinRepository
            from pathlib import Path
            
            # Delete from database
            success = CardBinRepository.delete(bin_to_delete)
            
            # Also delete from file
            bin_file = Path("card_bin.txt")
            if bin_file.exists():
                with open(bin_file, 'r') as f:
                    lines = f.readlines()
                with open(bin_file, 'w') as f:
                    for line in lines:
                        if line.strip() != bin_to_delete:
                            f.write(line)
            
            await query.edit_message_text(
                f"✅ Đã xóa BIN: {bin_to_delete}",
                reply_markup=get_bin_management_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lỗi khi xóa BIN: {str(e)}",
                reply_markup=get_bin_management_keyboard()
            )
    
    elif data == "bin_delete_all_confirm":
        keyboard = [
            [InlineKeyboardButton("⚠️ XÁC NHẬN XÓA TẤT CẢ", callback_data="bin_delete_all_yes")],
            [InlineKeyboardButton("❌ Hủy", callback_data="bin_delete_menu")]
        ]
        await query.edit_message_text(
            """
⚠️ CẢNH BÁO!

Bạn có chắc muốn xóa TẤT CẢ BIN?
Hành động này KHÔNG THỂ hoàn tác!
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "bin_delete_all_yes":
        try:
            from database.repository import CardBinRepository
            from pathlib import Path
            
            # Delete all from database
            count = CardBinRepository.delete_all()
            
            # Clear file
            bin_file = Path("card_bin.txt")
            if bin_file.exists():
                bin_file.write_text("")
            
            await query.edit_message_text(
                f"✅ Đã xóa tất cả {count} BIN!",
                reply_markup=get_bin_management_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lỗi: {str(e)}",
                reply_markup=get_bin_management_keyboard()
            )
    
    # Pagination handlers for BIN selection
    elif data.startswith("bin_select_page_"):
        page = int(data.split("_")[-1])
        bins = load_all_bins()
        
        workspace_name = context.user_data.get('workspace_name', 'N/A')
        
        await query.edit_message_text(
            f"""
✅ Workspace: {workspace_name}

Chọn BIN để thử thanh toán:
(Có {len(bins)} BIN trong hệ thống)
""",
            reply_markup=get_bin_selection_keyboard(bins, page)
        )
    
    # Pagination handlers for BIN deletion
    elif data.startswith("bin_delete_page_"):
        page = int(data.split("_")[-1])
        bins = load_all_bins()
        
        await query.edit_message_text(
            f"🗑️ Chọn BIN muốn xóa:\n\n📊 Tổng: {len(bins)} BIN",
            reply_markup=get_bin_list_delete_keyboard(bins, page)
        )
    
    # No-op for page info button
    elif data == "noop":
        await query.answer()
        return
    
    elif data == "help":
        await query.edit_message_text(
            HELP_MESSAGE,
            reply_markup=get_back_keyboard()
        )
    
    elif data == "back":
        await query.edit_message_text(
            WELCOME_MESSAGE,
            reply_markup=get_main_menu_keyboard()
        )
    
    # Registration callbacks
    elif data.startswith("register_"):
        # Clear any previous context
        context.user_data.clear()
        
        count_str = data.split("_")[1]
        
        if count_str == "custom":
            await query.edit_message_text(
                "Gửi số lượng tài khoản muốn đăng ký (1-100):"
            )
            context.user_data['waiting_for'] = 'register_count'
        else:
            count = int(count_str)
            context.user_data['register_count'] = count
            # Do NOT set action for registration
            await query.edit_message_text(
                f"Xác nhận đăng ký {count} tài khoản?",
                reply_markup=get_confirmation_keyboard()
            )
    
    # Account selection callbacks
    elif data.startswith("select_account_"):
        # Clear any previous context
        context.user_data.clear()
        
        index = int(data.split("_")[2])
        accounts = load_accounts()
        
        if index < len(accounts):
            context.user_data['selected_account'] = index
            context.user_data['action'] = 'upgrade'  # Mark this as upgrade action
            await query.edit_message_text(
                f"Đã chọn: {accounts[index]['email']}\n\nNhập tên workspace:"
            )
            context.user_data['waiting_for'] = 'workspace_name'
    
    # BIN selection callbacks
    elif data.startswith("select_bin_"):
        bin_value = data.split("_", 2)[2]
        
        if bin_value == "all":
            context.user_data['selected_bin'] = 'all'
            await query.edit_message_text(
                "🎲 Đã chọn: Thử tất cả BIN\n\nMỗi BIN thử bao nhiêu thẻ?",
                reply_markup=get_card_quantity_keyboard()
            )
        else:
            context.user_data['selected_bin'] = bin_value
            await query.edit_message_text(
                f"💳 Đã chọn BIN: {bin_value}\n\nThử bao nhiêu thẻ với BIN này?",
                reply_markup=get_card_quantity_keyboard()
            )
    
    # Card quantity callbacks
    elif data.startswith("card_qty_"):
        qty_str = data.split("_")[2]
        
        if qty_str == "custom":
            await query.edit_message_text(
                "Nhập số lượng thẻ muốn thử (1-50):"
            )
            context.user_data['waiting_for'] = 'card_quantity'
        else:
            qty = int(qty_str)
            context.user_data['card_quantity'] = qty
            
            # Show confirmation
            account_index = context.user_data.get('selected_account')
            accounts = load_accounts()
            account_email = accounts[account_index].get('email', 'N/A') if account_index < len(accounts) else 'N/A'
            workspace_name = context.user_data.get('workspace_name', 'N/A')
            selected_bin = context.user_data.get('selected_bin', 'N/A')
            
            if selected_bin == 'all':
                bin_text = "Tất cả BIN"
                card_text = f"{qty} thẻ/BIN"
            else:
                bin_text = f"BIN {selected_bin}"
                card_text = f"{qty} thẻ"
            
            await query.edit_message_text(
                f"""
💳 Xác nhận nâng cấp

📧 Tài khoản: {account_email}
🏢 Workspace: {workspace_name}
💳 BIN: {bin_text}
🎯 Số thẻ: {card_text}

Bắt đầu thanh toán?
""",
                reply_markup=get_confirmation_keyboard()
            )
    
    # Confirmation callbacks
    elif data == "confirm_yes":
        # Check if this is registration or payment confirmation
        action = context.user_data.get('action')
        
        if action == 'upgrade':
            # This is payment confirmation
            # Verify we have all required data
            if not all(k in context.user_data for k in ['selected_account', 'workspace_name', 'selected_bin', 'card_quantity']):
                await query.edit_message_text(
                    "❌ Lỗi: Thiếu thông tin. Vui lòng thử lại.",
                    reply_markup=get_main_menu_keyboard()
                )
                context.user_data.clear()
                return
            
            await perform_payment(query, context)
            
        elif 'register_count' in context.user_data:
            # This is registration confirmation
            count = context.user_data['register_count']
            await query.edit_message_text(f"🔄 Đang đăng ký {count} tài khoản...")
            
            # Start registration in background
            await perform_registration(query, context, count)
            
        else:
            # Unknown action - clear and return to menu
            await query.edit_message_text(
                "❌ Lỗi: Không xác định được hành động. Vui lòng thử lại.",
                reply_markup=get_main_menu_keyboard()
            )
            context.user_data.clear()
    
    elif data == "confirm_no":
        await query.edit_message_text(
            "❌ Đã hủy",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()


async def perform_registration(query, context, count: int):
    """Perform registration"""
    success_count = 0
    
    for i in range(count):
        try:
            await query.edit_message_text(
                f"🔄 Đang đăng ký tài khoản {i+1}/{count}..."
            )
            
            with ChatGPTRegistrationBot() as bot:
                result = bot.register()
                
                if result.success:
                    save_account(result.to_dict())
                    success_count += 1
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=format_registration_result(result),
                        parse_mode='Markdown'
                    )
        except Exception as e:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Lỗi tài khoản {i+1}: {str(e)}"
            )
    
    # Send summary with main menu
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"""
📊 Hoàn thành!

✅ Thành công: {success_count}/{count}
❌ Thất bại: {count - success_count}
""",
        reply_markup=get_main_menu_keyboard()
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text
    
    # Check for cancel command
    if text == '/cancel':
        waiting_for = context.user_data.get('waiting_for')
        context.user_data.clear()
        
        # Return to appropriate menu based on what was being waited for
        if waiting_for == 'proxy_url':
            await update.message.reply_text(
                "❌ Đã hủy",
                reply_markup=get_proxy_management_keyboard()
            )
        elif waiting_for == 'bin_number':
            await update.message.reply_text(
                "❌ Đã hủy",
                reply_markup=get_bin_management_keyboard()
            )
        elif waiting_for in ['register_count', 'workspace_name', 'confirm_payment']:
            await update.message.reply_text(
                "❌ Đã hủy",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Đã hủy",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    # Check if waiting for input
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'proxy_url':
        # Check if user wants batch mode
        if text.lower() == 'batch':
            context.user_data['proxy_batch_mode'] = True
            context.user_data['proxy_batch'] = []
            await update.message.reply_text(
                """
📦 Chế độ hàng loạt đã BẬT

Gửi proxy (có thể gửi nhiều message):
user:pass@host:port

Khi gửi xong, gửi "done" để hoàn tất
Hoặc /cancel để hủy
"""
            )
            return
        
        # Check if in batch mode
        if context.user_data.get('proxy_batch_mode'):
            if text.lower() == 'done':
                # Process all collected proxies
                all_proxies = context.user_data.get('proxy_batch', [])
                
                if not all_proxies:
                    await update.message.reply_text(
                        "❌ Chưa có proxy nào!"
                    )
                    return
                
                await update.message.reply_text(
                    f"🔄 Đang xử lý {len(all_proxies)} proxy..."
                )
                
                success_count = 0
                fail_count = 0
                
                for i, proxy_line in enumerate(all_proxies, 1):
                    try:
                        # Auto add http://
                        if not proxy_line.startswith('http://') and not proxy_line.startswith('https://') and not proxy_line.startswith('socks5://'):
                            proxy_url = f"http://{proxy_line}"
                            proxy_type = 'http'
                        elif proxy_line.startswith('socks5://'):
                            proxy_url = proxy_line
                            proxy_type = 'socks5'
                        else:
                            proxy_url = proxy_line
                            proxy_type = 'http'
                        
                        # Validate format
                        if '@' not in proxy_url or proxy_url.count(':') < 3:
                            fail_count += 1
                            continue
                        
                        # Save to database
                        from database.repository import ProxyRepository
                        ProxyRepository.create(
                            proxy_url=proxy_url,
                            proxy_type=proxy_type,
                            country=None,
                            notes="Added via Telegram bot (batch)"
                        )
                        
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        log.error(f"Failed to add proxy {i}: {e}")
                
                # Clear batch mode
                context.user_data.pop('proxy_batch_mode', None)
                context.user_data.pop('proxy_batch', None)
                context.user_data.pop('waiting_for', None)
                
                # Send summary
                summary = f"""
✅ Hoàn thành!

📊 Kết quả:
• Tổng: {len(all_proxies)}
• Thành công: {success_count}
• Thất bại: {fail_count}

💾 Đã lưu vào database
"""
                
                await update.message.reply_text(
                    summary,
                    reply_markup=get_proxy_management_keyboard()
                )
                return
            
            else:
                # Collect proxies from this message
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                if 'proxy_batch' not in context.user_data:
                    context.user_data['proxy_batch'] = []
                
                context.user_data['proxy_batch'].extend(lines)
                
                total = len(context.user_data['proxy_batch'])
                await update.message.reply_text(
                    f"✅ Đã nhận {len(lines)} proxy\n📦 Tổng: {total}\n\nGửi thêm hoặc gửi 'done' để hoàn tất"
                )
                return
        
        # Normal mode - process immediately
        try:
            proxy_input = text.strip()
            
            # Split by newline to get all proxies
            lines = [line.strip() for line in proxy_input.split('\n') if line.strip()]
            
            if not lines:
                await update.message.reply_text(
                    "❌ Không tìm thấy proxy nào!"
                )
                return
            
            # Show processing message
            if len(lines) > 1:
                processing_msg = await update.message.reply_text(
                    f"🔄 Đang xử lý {len(lines)} proxy..."
                )
            
            success_count = 0
            fail_count = 0
            
            for i, proxy_line in enumerate(lines, 1):
                try:
                    # Auto add http:// if not present
                    if not proxy_line.startswith('http://') and not proxy_line.startswith('https://') and not proxy_line.startswith('socks5://'):
                        proxy_url = f"http://{proxy_line}"
                        proxy_type = 'http'
                    elif proxy_line.startswith('socks5://'):
                        proxy_url = proxy_line
                        proxy_type = 'socks5'
                    else:
                        proxy_url = proxy_line
                        proxy_type = 'http'
                    
                    # Validate format
                    if '@' not in proxy_url or proxy_url.count(':') < 3:
                        fail_count += 1
                        continue
                    
                    # Save to database
                    from database.repository import ProxyRepository
                    ProxyRepository.create(
                        proxy_url=proxy_url,
                        proxy_type=proxy_type,
                        country=None,
                        notes="Added via Telegram bot"
                    )
                    
                    success_count += 1
                    
                    # Update progress every 10 proxies
                    if len(lines) > 10 and i % 10 == 0:
                        try:
                            await processing_msg.edit_text(
                                f"🔄 Đang xử lý... {i}/{len(lines)}"
                            )
                        except:
                            pass
                    
                except Exception as e:
                    fail_count += 1
                    log.error(f"Failed to add proxy {i}: {e}")
            
            context.user_data.pop('waiting_for')
            
            # Send summary
            summary = f"""
✅ Hoàn thành!

📊 Kết quả:
• Tổng: {len(lines)}
• Thành công: {success_count}
• Thất bại: {fail_count}

💾 Đã lưu vào database
"""
            
            await update.message.reply_text(
                summary,
                reply_markup=get_proxy_management_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi: {str(e)}\n\nVui lòng thử lại.",
                reply_markup=get_proxy_management_keyboard()
            )
            context.user_data.pop('waiting_for', None)
    
    elif waiting_for == 'bin_number':
        try:
            # Split by newlines to support multiple BINs
            bin_lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if not bin_lines:
                await update.message.reply_text(
                    "❌ Không tìm thấy BIN nào!\n\nVui lòng thử lại hoặc /cancel để hủy."
                )
                return
            
            success_count = 0
            fail_count = 0
            failed_bins = []
            
            for bin_number in bin_lines:
                # Validate BIN (6-8 digits)
                if not bin_number.isdigit() or len(bin_number) < 6 or len(bin_number) > 8:
                    fail_count += 1
                    failed_bins.append(f"{bin_number} (không hợp lệ)")
                    continue
                
                # Save to database
                try:
                    from database.repository import CardBinRepository
                    CardBinRepository.create(bin_number)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_bins.append(f"{bin_number} (lỗi DB)")
                    log.error(f"Failed to save BIN {bin_number}: {e}")
                
                # Also save to file as backup
                try:
                    from pathlib import Path
                    bin_file = Path("card_bin.txt")
                    
                    # Read existing BINs
                    existing_bins = []
                    if bin_file.exists():
                        with open(bin_file, 'r') as f:
                            existing_bins = [line.strip() for line in f if line.strip()]
                    
                    # Add if not exists
                    if bin_number not in existing_bins:
                        with open(bin_file, 'a') as f:
                            f.write(f"{bin_number}\n")
                except:
                    pass
            
            context.user_data.pop('waiting_for')
            
            # Build result message
            result_msg = f"""
✅ Hoàn thành!

📊 Kết quả:
• Tổng: {len(bin_lines)}
• Thành công: {success_count}
• Thất bại: {fail_count}
"""
            
            if failed_bins and len(failed_bins) <= 5:
                result_msg += f"\n❌ Lỗi:\n"
                for fb in failed_bins:
                    result_msg += f"• {fb}\n"
            
            await update.message.reply_text(
                result_msg,
                reply_markup=get_bin_management_keyboard()
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi: {str(e)}\n\nVui lòng thử lại.",
                reply_markup=get_bin_management_keyboard()
            )
            context.user_data.pop('waiting_for', None)
    
    elif waiting_for == 'register_count':
        try:
            count = int(text)
            if 1 <= count <= 100:
                context.user_data['register_count'] = count
                context.user_data.pop('waiting_for')
                await update.message.reply_text(
                    f"Xác nhận đăng ký {count} tài khoản?",
                    reply_markup=get_confirmation_keyboard()
                )
            else:
                await update.message.reply_text(
                    "Số lượng phải từ 1-100",
                    reply_markup=get_main_menu_keyboard()
                )
        except:
            await update.message.reply_text(
                "Vui lòng nhập số hợp lệ",
                reply_markup=get_main_menu_keyboard()
            )
    
    elif waiting_for == 'workspace_name':
        workspace_name = text.strip()
        context.user_data['workspace_name'] = workspace_name
        context.user_data.pop('waiting_for')
        
        # Load BINs and show selection
        bins = load_all_bins()
        
        if not bins:
            await update.message.reply_text(
                "❌ Không có BIN nào trong hệ thống!\n\nVui lòng thêm BIN trước.",
                reply_markup=get_main_menu_keyboard()
            )
            context.user_data.clear()
            return
        
        await update.message.reply_text(
            f"""
✅ Workspace: {workspace_name}

Chọn BIN để thử thanh toán:
(Có {len(bins)} BIN trong hệ thống)
""",
            reply_markup=get_bin_selection_keyboard(bins)
        )
    
    elif waiting_for == 'card_quantity':
        try:
            qty = int(text.strip())
            if 1 <= qty <= 50:
                context.user_data['card_quantity'] = qty
                context.user_data.pop('waiting_for')
                
                # Show confirmation
                account_index = context.user_data.get('selected_account')
                accounts = load_accounts()
                account_email = accounts[account_index].get('email', 'N/A') if account_index < len(accounts) else 'N/A'
                workspace_name = context.user_data.get('workspace_name', 'N/A')
                selected_bin = context.user_data.get('selected_bin', 'N/A')
                
                if selected_bin == 'all':
                    bin_text = "Tất cả BIN"
                    card_text = f"{qty} thẻ/BIN"
                else:
                    bin_text = f"BIN {selected_bin}"
                    card_text = f"{qty} thẻ"
                
                await update.message.reply_text(
                    f"""
💳 Xác nhận nâng cấp

📧 Tài khoản: {account_email}
🏢 Workspace: {workspace_name}
💳 BIN: {bin_text}
🎯 Số thẻ: {card_text}

Bắt đầu thanh toán?
""",
                    reply_markup=get_confirmation_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Số lượng phải từ 1-50. Vui lòng nhập lại:"
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Vui lòng nhập số hợp lệ (1-50):"
            )


async def perform_payment(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    """Perform payment for selected account with multiple cards/BINs"""
    try:
        account_index = context.user_data.get('selected_account')
        workspace_name = context.user_data.get('workspace_name')
        selected_bin = context.user_data.get('selected_bin', 'all')
        card_quantity = context.user_data.get('card_quantity', 1)
        
        accounts = load_accounts()
        account = accounts[account_index]
        
        # Determine chat_id
        if hasattr(query_or_update, 'message') and hasattr(query_or_update, 'edit_message_text'):
            chat_id = query_or_update.message.chat_id
        else:
            chat_id = query_or_update.message.chat_id
        
        # Send initial progress message
        progress_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔄 Đang khởi động...\n\n💳 BIN: {selected_bin}\n🎯 Số thẻ: {card_quantity}"
        )
        
        # Get access token
        from utils.token_helper import get_access_token
        cookies = account.get('cookies', {})
        access_token = get_access_token(cookies)
        
        if not access_token:
            await progress_msg.edit_text("❌ Không lấy được access token")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Quay lại menu",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Load BINs
        all_bins = load_all_bins()
        if not all_bins:
            await progress_msg.edit_text("❌ Không có BIN")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Quay lại menu",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Determine which BINs to use
        if selected_bin == 'all':
            bins_to_try = all_bins
        else:
            bins_to_try = [selected_bin]
        
        # Track results
        total_attempts = 0
        success_count = 0
        captcha_count = 0
        failed_count = 0
        error_details = []
        
        total_cards = len(bins_to_try) * card_quantity
        
        # Try each BIN
        for bin_idx, bin_number in enumerate(bins_to_try):
            # Try multiple cards for this BIN
            for card_num in range(card_quantity):
                total_attempts += 1
                
                # Update progress bar
                progress = total_attempts / total_cards
                bar_length = 10
                filled = int(bar_length * progress)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                progress_text = f"""
🔄 Đang xử lý thanh toán...

📊 Tiến độ: {bar} {int(progress * 100)}%
💳 BIN hiện tại: {bin_number}
🎯 Thẻ: {total_attempts}/{total_cards}

✅ Thành công: {success_count}
⚠️ Captcha: {captcha_count}
❌ Thất bại: {failed_count}
"""
                
                try:
                    await progress_msg.edit_text(progress_text)
                except:
                    pass  # Ignore if message is same
                
                # Generate Korean identity
                korean_identity = generate_korean_identity()
                
                # Generate card
                card_info = generate_full_card(bin_number)
                
                # Select random Korean address from database
                from database.repository import KoreanAddressRepository
                selected_address = KoreanAddressRepository.get_random_address()
                
                # Fallback to file if database is empty
                if not selected_address:
                    from utils.korean_address import get_random_korean_address
                    selected_address = get_random_korean_address()
                
                # Format address for display
                address_display = f"{selected_address['city']}, {selected_address['line2']}"
                
                # Update progress with actual address
                progress_text = f"""
🔄 Đang xử lý thanh toán...

📊 Tiến độ: {bar} {int(progress * 100)}%
💳 BIN hiện tại: {bin_number}
🎯 Thẻ: {total_attempts}/{total_cards}
📍 Địa chỉ: {address_display}

✅ Thành công: {success_count}
⚠️ Captcha: {captcha_count}
❌ Thất bại: {failed_count}
"""
                
                try:
                    await progress_msg.edit_text(progress_text)
                except:
                    pass  # Ignore if message is same
                
                # Create payment config with selected address
                config = PaymentConfig(
                    workspace_name=workspace_name,
                    card_number=card_info['card_number'],
                    exp_month=card_info['exp_month'],
                    exp_year=card_info['exp_year'],
                    cvc=card_info['cvv'],
                    billing_name=korean_identity['name'],
                    billing_email=account.get('email'),
                    country='KR',
                    billing_address=selected_address
                )
                
                # Process payment
                try:
                    with ChatGPTPaymentBot(access_token, cookies) as payment_bot:
                        result = payment_bot.process_payment(config)
                        
                        # Save payment result to database
                        try:
                            PaymentRepository.create(
                                account_email=account.get('email'),
                                workspace_name=result.workspace_name,
                                checkout_session_id=result.checkout_session_id,
                                payment_method_id=result.payment_method_id,
                                payment_status=result.payment_status,
                                success=result.success,
                                error=result.error
                            )
                            
                            # Update BIN stats
                            if result.success:
                                CardBinRepository.update_success(bin_number)
                                success_count += 1
                                
                                # Success! Show final result
                                await progress_msg.edit_text(
                                    f"""
✅ THANH TOÁN THÀNH CÔNG!

💳 BIN: {bin_number}
🎯 Thẻ thử: {total_attempts}/{total_cards}

📊 Kết quả:
✅ Thành công: {success_count}
⚠️ Captcha: {captcha_count}
❌ Thất bại: {failed_count}
"""
                                )
                                
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text=format_payment_result(result),
                                    parse_mode='Markdown',
                                    reply_markup=get_main_menu_keyboard()
                                )
                                return
                            else:
                                CardBinRepository.update_fail(bin_number)
                                
                                # Check if captcha
                                if result.error and 'captcha' in result.error.lower():
                                    captcha_count += 1
                                else:
                                    failed_count += 1
                                    
                                # Store error for summary
                                if len(error_details) < 5:  # Keep only first 5 errors
                                    error_details.append(f"BIN {bin_number}: {result.error[:50]}")
                        except Exception as e:
                            log.error(f"Database error: {e}")
                            failed_count += 1
                
                except Exception as e:
                    failed_count += 1
                    if len(error_details) < 5:
                        error_details.append(f"BIN {bin_number}: {str(e)[:50]}")
        
        # All attempts failed - show summary
        summary_text = f"""
❌ Tất cả thử nghiệm đều thất bại

📊 Tổng kết:
🎯 Tổng thử: {total_attempts}
✅ Thành công: {success_count}
⚠️ Captcha challenge: {captcha_count}
❌ Thất bại: {failed_count}

🔍 Lỗi phổ biến:
"""
        
        for error in error_details:
            summary_text += f"\n• {error}"
        
        await progress_msg.edit_text(summary_text)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="Quay lại menu",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        try:
            await progress_msg.edit_text(f"❌ Lỗi: {str(e)}")
        except:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Lỗi: {str(e)}",
                reply_markup=get_main_menu_keyboard()
            )
    finally:
        context.user_data.clear()
