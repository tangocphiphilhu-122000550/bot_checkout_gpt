"""Entry point for Telegram Bot"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import from src.telegram_bot to avoid conflict with telegram library
from telegram_bot.bot import main

if __name__ == "__main__":
    main()
