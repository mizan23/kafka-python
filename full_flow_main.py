import threading
import time
import signal
import sys

from configuration import USERNAME, PASSWORD
from token_manager_automatic_refresh import TokenManager
from create_kafka_subscription import create_subscription
from renew_subscription import renew_subscription
from delete_subscription import delete_subscription
from kafka_consumer import start_kafka_consumer

subscription_id = None
token_mgr = None
stop_event = threading.Event()


def auto_renew_subscription(token_mgr, subscription_id, stop_event, interval=1800):
    while not stop_event.wait(interval):
        try:
            renew_subscription(token_mgr, subscription_id)
            print("🔁 Subscription renewed")
        except Exception as e:
            print("❌ Subscription renewal failed:", e)


def shutdown_handler(sig, frame):
    print("\n🛑 Shutting down...")
    stop_event.set()

    if subscription_id:
        delete_subscription(token_mgr, subscription_id)

    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)


if __name__ == "__main__":
    token_mgr = TokenManager(USERNAME, PASSWORD)

    subscription_id, topic_id = create_subscription(token_mgr)

    threading.Thread(
        target=auto_renew_subscription,
        args=(token_mgr, subscription_id, stop_event),
        daemon=True
    ).start()

    start_kafka_consumer(topic_id, stop_event)
