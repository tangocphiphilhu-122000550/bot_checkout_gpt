"""Main Telegram Bot"""
import os
import sys
from pathlib import Path

# Add parent directory to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import telegram library
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters
)

# Import local handlers
from telegram_bot.handlers import (
    start_command, help_command, register_command,
    accounts_command, upgrade_command, config_command,
    status_command, button_callback, message_handler
)
from utils.logger import log


class TelegramBot:
    """Telegram Bot for ChatGPT Auto Bot"""
    
    def __init__(self, token: str, admin_ids: list = None):
        """
        Initialize Telegram bot
        
        Args:
            token: Telegram bot token
            admin_ids: List of admin user IDs (optional)
        """
        self.token = token
        self.admin_ids = admin_ids or []
        self.app = None
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("help", help_command))
        self.app.add_handler(CommandHandler("register", register_command))
        self.app.add_handler(CommandHandler("accounts", accounts_command))
        self.app.add_handler(CommandHandler("upgrade", upgrade_command))
        self.app.add_handler(CommandHandler("config", config_command))
        self.app.add_handler(CommandHandler("status", status_command))
        
        # Callback query handler (for buttons)
        self.app.add_handler(CallbackQueryHandler(button_callback))
        
        # Message handler (for text input)
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            message_handler
        ))
    
    async def post_init(self, application: Application):
        """Post initialization - send startup message to admins"""
        if self.admin_ids:
            for admin_id in self.admin_ids:
                try:
                    await application.bot.send_message(
                        chat_id=admin_id,
                        text="🤖 Bot đã khởi động thành công!"
                    )
                except Exception as e:
                    log.warning(f"Could not send startup message to admin {admin_id}: {e}")
    
    def run(self):
        """Run the bot"""
        log.info("=" * 60)
        log.info("🤖 STARTING TELEGRAM BOT")
        log.info("=" * 60)
        log.info(f"Token: {self.token[:10]}...")
        log.info(f"Admin IDs: {self.admin_ids}")
        log.info("")
        
        # Create application
        self.app = Application.builder().token(self.token).post_init(self.post_init).build()
        
        # Setup handlers
        self.setup_handlers()
        
        log.success("✅ Bot handlers configured")
        log.info("🚀 Starting polling...")
        log.info("")
        
        # Start polling
        self.app.run_polling(allowed_updates=["message", "callback_query"])


def main():
    """Main entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        log.error("❌ TELEGRAM_BOT_TOKEN not found in .env")
        log.info("💡 Add TELEGRAM_BOT_TOKEN=your_token_here to .env")
        sys.exit(1)
    
    # Get admin IDs (optional)
    admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
    admin_ids = []
    if admin_ids_str:
        try:
            admin_ids = [int(id.strip()) for id in admin_ids_str.split(",")]
        except:
            log.warning("⚠ Could not parse TELEGRAM_ADMIN_IDS")
    
    # Create and run bot
    bot = TelegramBot(token, admin_ids)
    bot.run()


if __name__ == "__main__":
    main()
