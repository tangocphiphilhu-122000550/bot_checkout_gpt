"""Migrate proxies from proxy.txt to Supabase database"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.repository import ProxyRepository
from database.connection import init_database
from utils.logger import log


def parse_proxy_url(proxy_line: str) -> dict:
    """
    Parse proxy URL and extract info
    
    Formats supported:
    - http://user:pass@host:port
    - socks5://user:pass@host:port
    - host:port:user:pass
    """
    proxy_line = proxy_line.strip()
    
    if not proxy_line or proxy_line.startswith('#'):
        return None
    
    # Format: protocol://user:pass@host:port
    if '://' in proxy_line:
        parts = proxy_line.split('://')
        proxy_type = parts[0]
        rest = parts[1]
        
        return {
            'proxy_url': proxy_line,
            'proxy_type': proxy_type,
            'country': None  # Can't detect from URL
        }
    
    # Format: host:port:user:pass
    elif proxy_line.count(':') == 3:
        host, port, user, password = proxy_line.split(':')
        proxy_url = f"http://{user}:{password}@{host}:{port}"
        
        return {
            'proxy_url': proxy_url,
            'proxy_type': 'http',
            'country': None
        }
    
    # Format: host:port
    elif proxy_line.count(':') == 1:
        host, port = proxy_line.split(':')
        proxy_url = f"http://{host}:{port}"
        
        return {
            'proxy_url': proxy_url,
            'proxy_type': 'http',
            'country': None
        }
    
    else:
        log.warning(f"⚠ Unknown proxy format: {proxy_line}")
        return None


def main():
    """Migrate proxies from proxy.txt to database"""
    
    log.info("=" * 60)
    log.info("🌐 MIGRATING PROXIES FROM TXT TO DATABASE")
    log.info("=" * 60)
    log.info("")
    
    # Check if proxy.txt exists
    proxy_file = Path("proxy.txt")
    if not proxy_file.exists():
        log.warning("⚠ proxy.txt not found")
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
    
    # Load proxies from file
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        log.info(f"📄 Found {len(lines)} lines in proxy.txt")
        log.info("")
    except Exception as e:
        log.error(f"❌ Failed to read proxy.txt: {e}")
        sys.exit(1)
    
    # Migrate
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, line in enumerate(lines, 1):
        proxy_info = parse_proxy_url(line)
        
        if not proxy_info:
            skip_count += 1
            continue
        
        proxy_url = proxy_info['proxy_url']
        
        try:
            # Check if already exists
            existing = ProxyRepository.get_all()
            if any(p.proxy_url == proxy_url for p in existing):
                log.warning(f"⏭️  [{i}/{len(lines)}] Skipped (exists): {proxy_url}")
                skip_count += 1
                continue
            
            # Create proxy
            ProxyRepository.create(
                proxy_url=proxy_url,
                proxy_type=proxy_info['proxy_type'],
                country=proxy_info['country'],
                notes="Migrated from proxy.txt"
            )
            
            log.success(f"✅ [{i}/{len(lines)}] Migrated: {proxy_url}")
            success_count += 1
            
        except Exception as e:
            log.error(f"❌ [{i}/{len(lines)}] Failed: {proxy_url} - {e}")
            fail_count += 1
    
    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("📊 MIGRATION SUMMARY")
    log.info("=" * 60)
    log.info(f"Total lines: {len(lines)}")
    log.info(f"✅ Migrated: {success_count}")
    log.info(f"⏭️  Skipped: {skip_count}")
    log.info(f"❌ Failed: {fail_count}")
    log.info("=" * 60)
    
    if success_count > 0:
        log.info("")
        log.success("🎉 Migration completed successfully!")
        log.info("")
        log.info("You can now:")
        log.info("  1. Backup proxy.txt: mv proxy.txt proxy.txt.bak")
        log.info("  2. View proxies in Supabase dashboard")
        log.info("  3. Use ProxyRepository in your code")
        log.info("")


if __name__ == "__main__":
    main()
