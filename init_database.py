"""Initialize Supabase database tables"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.connection import init_database
from utils.logger import log


def main():
    """Initialize database"""
    log.info("=" * 60)
    log.info("🗄️  INITIALIZING DATABASE")
    log.info("=" * 60)
    log.info("")
    
    try:
        init_database()
        
        log.info("")
        log.info("=" * 60)
        log.success("✅ DATABASE INITIALIZED SUCCESSFULLY!")
        log.info("=" * 60)
        log.info("")
        log.info("Tables created:")
        log.info("  • accounts - Store ChatGPT accounts")
        log.info("  • payments - Store payment transactions")
        log.info("  • card_bins - Store card BINs with success/fail stats")
        log.info("  • proxies - Store proxies with performance tracking")
        log.info("  • korean_addresses - Store Korean addresses for billing")
        log.info("  • logs - Store application logs")
        log.info("")
        log.info("You can now run:")
        log.info("  • python main.py - CLI mode")
        log.info("  • python bot_main.py - Telegram bot mode")
        log.info("  • python migrate_json_to_db.py - Migrate accounts")
        log.info("  • python migrate_proxy_to_db.py - Migrate proxies")
        log.info("  • python migrate_addresses_to_db.py - Migrate addresses")
        log.info("")
        
    except Exception as e:
        log.error("")
        log.error("=" * 60)
        log.error("❌ DATABASE INITIALIZATION FAILED")
        log.error("=" * 60)
        log.error(f"Error: {e}")
        log.error("")
        log.error("Please check:")
        log.error("  1. DATABASE_URL in .env is correct")
        log.error("  2. Database is accessible")
        log.error("  3. You have proper permissions")
        log.error("")
        sys.exit(1)


if __name__ == "__main__":
    main()
