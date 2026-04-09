"""Entry point for Telegram Bot"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Start health check server for Render (if PORT env var exists)
if os.getenv("PORT"):
    from health_server import start_health_server
    port = int(os.getenv("PORT", 10000))
    start_health_server(port)
    print(f"🌐 Health server running on port {port} for Render")

# Import from src.telegram_bot to avoid conflict with telegram library
from telegram_bot.bot import main

if __name__ == "__main__":
    main()
