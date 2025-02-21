import os
import time
import subprocess

# Path to your bot script
BOT_SCRIPT = os.path.expanduser("~/Documents/kraken_test.py")

def is_bot_running():
    """Check if the bot process is running."""
    try:
        result = subprocess.run(["pgrep", "-f", "kraken_test.py"], capture_output=True, text=True)
        return result.stdout.strip() != ""
    except Exception as e:
        print(f"❌ Error checking bot process: {e}")
        return False

def restart_bot():
    """Restart the bot if it's not running."""
    print("🔄 Restarting the bot...")
    subprocess.Popen(["python3", BOT_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Watchdog loop
print("🚀 Watchdog started. Monitoring bot status...")
while True:
    if not is_bot_running():
        restart_bot()
    time.sleep(60)  # Check every 60 seconds

