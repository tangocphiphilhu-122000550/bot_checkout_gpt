"""Clear Telegram bot webhook to allow polling"""
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

def clear_webhook():
    """Clear webhook and enable polling mode"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        sys.exit(1)
    
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    try:
        print("🔄 Clearing webhook...")
        response = httpx.post(url, params={"drop_pending_updates": True}, timeout=30)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook cleared successfully!")
            print(f"   Description: {result.get('description', 'N/A')}")
            
            # Get bot info
            info_url = f"https://api.telegram.org/bot{token}/getMe"
            info_response = httpx.get(info_url, timeout=30)
            info = info_response.json()
            
            if info.get("ok"):
                bot_info = info.get("result", {})
                print(f"\n🤖 Bot Info:")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   Name: {bot_info.get('first_name')}")
                print(f"   ID: {bot_info.get('id')}")
            
            print("\n✅ Bot is now ready for polling mode!")
        else:
            print(f"❌ Failed: {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_webhook()
