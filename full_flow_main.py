import threading
import signal
import sys
import atexit

from configuration import USERNAME, PASSWORD
from token_manager_automatic_refresh import TokenManager
from create_kafka_subscription import create_subscription
from renew_subscription import renew_subscription
from delete_subscription import delete_subscription
from kafka_consumer import start_kafka_consumer
from revoke_token import revoke_token


# -------------------------------
# Global state
# -------------------------------

stop_event = threading.Event()
subscription_id = None
token_mgr = None
cleanup_done = False


# -------------------------------
# Cleanup logic (SAFE + IDPOTENT)
# -------------------------------

def cleanup():
    global cleanup_done
    if cleanup_done:
        return
    cleanup_done = True

    print("\n🧹 Cleaning up NSP resources...")
    stop_event.set()

    if subscription_id:
        try:
            delete_subscription(token_mgr, subscription_id)
        except Exception as e:
            print("⚠️ Failed to delete subscription:", e)

    if token_mgr and token_mgr.access_token:
        try:
            revoke_token(token_mgr.access_token)
        except Exception as e:
            print("⚠️ Failed to revoke token:", e)


# -------------------------------
# Signal handlers
# -------------------------------

def shutdown_handler(sig, frame):
    print("\n🛑 Shutdown signal received")
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ✅ Run cleanup even on unhandled exception
atexit.register(cleanup)


# -------------------------------
# Auto-renew thread
# -------------------------------

def auto_renew_subscription(token_mgr, subscription_id, stop_event, interval=1800):
    while not stop_event.wait(interval):
        try:
            renew_subscription(token_mgr, subscription_id)
            print("🔁 Subscription renewed")
        except Exception as e:
            print("❌ Subscription renewal failed:", e)


# -------------------------------
# Main
# -------------------------------

if __name__ == "__main__":

    try:
        token_mgr = TokenManager(USERNAME, PASSWORD)

        subscription_id, topic_id = create_subscription(token_mgr)

        threading.Thread(
            target=auto_renew_subscription,
            args=(token_mgr, subscription_id, stop_event),
            daemon=True
        ).start()

        start_kafka_consumer(topic_id, stop_event)

    except Exception as e:
        print("❌ Fatal error:", e)
        cleanup()
        sys.exit(1)
