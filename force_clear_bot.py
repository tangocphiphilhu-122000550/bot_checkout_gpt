"""Force clear all bot connections"""
import os
import sys
import httpx
from dotenv import load_dotenv
import time

load_dotenv()

def force_clear():
    """Force clear webhook and drop all pending updates"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        sys.exit(1)
    
    print("🔄 Force clearing bot connections...")
    
    # Step 1: Delete webhook with drop_pending_updates
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        response = httpx.post(url, params={"drop_pending_updates": True}, timeout=30)
        result = response.json()
        print(f"✅ Webhook deleted: {result.get('description', 'OK')}")
    except Exception as e:
        print(f"⚠️ Webhook delete error: {e}")
    
    time.sleep(2)
    
    # Step 2: Get and clear pending updates
    get_updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        print("🔄 Clearing pending updates...")
        response = httpx.post(get_updates_url, params={"offset": -1, "timeout": 1}, timeout=30)
        result = response.json()
        
        if result.get("ok"):
            updates = result.get("result", [])
            if updates:
                last_update_id = updates[-1].get("update_id")
                # Clear all by setting offset to last_update_id + 1
                httpx.post(get_updates_url, params={"offset": last_update_id + 1, "timeout": 1}, timeout=30)
                print(f"✅ Cleared {len(updates)} pending updates")
            else:
                print("✅ No pending updates")
        else:
            print(f"⚠️ Get updates error: {result}")
    except Exception as e:
        print(f"⚠️ Clear updates error: {e}")
    
    time.sleep(2)
    
    # Step 3: Verify bot info
    info_url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = httpx.get(info_url, timeout=30)
        info = response.json()
        
        if info.get("ok"):
            bot_info = info.get("result", {})
            print(f"\n🤖 Bot Info:")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   Name: {bot_info.get('first_name')}")
            print(f"   ID: {bot_info.get('id')}")
            print(f"\n✅ Bot is ready for polling!")
        else:
            print(f"❌ Bot info error: {info}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_clear()
