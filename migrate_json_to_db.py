"""Migrate accounts from JSON file to Supabase database"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.repository import AccountRepository
from database.connection import init_database
from utils.logger import log


def main():
    """Migrate accounts from accounts.json to database"""
    
    log.info("=" * 60)
    log.info("📦 MIGRATING ACCOUNTS FROM JSON TO DATABASE")
    log.info("=" * 60)
    log.info("")
    
    # Check if JSON file exists
    json_file = Path("accounts.json")
    if not json_file.exists():
        log.warning("⚠ accounts.json not found")
        log.info("Nothing to migrate")
        return
    
    # Initialize database
    try:
        init_database()
        log.success("✅ Database connected")
        log.info("")
    except Exception as e:
        log.error(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Load JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        log.info(f"📄 Found {len(accounts)} accounts in JSON")
        log.info("")
    except Exception as e:
        log.error(f"❌ Failed to read JSON: {e}")
        sys.exit(1)
    
    # Migrate
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, acc in enumerate(accounts, 1):
        email = acc.get('email', 'Unknown')
        
        try:
            # Check if already exists
            existing = AccountRepository.get_by_email(email)
            if existing:
                log.warning(f"⏭️  [{i}/{len(accounts)}] Skipped (exists): {email}")
                skip_count += 1
                continue
            
            # Create account
            AccountRepository.create(
                email=acc['email'],
                password=acc['password'],
                name=acc.get('name'),
                birthdate=acc.get('birthdate'),
                cookies=acc.get('cookies')
            )
            
            log.success(f"✅ [{i}/{len(accounts)}] Migrated: {email}")
            success_count += 1
            
        except Exception as e:
            log.error(f"❌ [{i}/{len(accounts)}] Failed: {email} - {e}")
            fail_count += 1
    
    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("📊 MIGRATION SUMMARY")
    log.info("=" * 60)
    log.info(f"Total: {len(accounts)}")
    log.info(f"✅ Migrated: {success_count}")
    log.info(f"⏭️  Skipped: {skip_count}")
    log.info(f"❌ Failed: {fail_count}")
    log.info("=" * 60)
    
    if success_count > 0:
        log.info("")
        log.success("🎉 Migration completed successfully!")
        log.info("")
        log.info("You can now:")
        log.info("  1. Backup accounts.json: mv accounts.json accounts.json.bak")
        log.info("  2. Run bot: python bot_main.py")
        log.info("")


if __name__ == "__main__":
    main()
