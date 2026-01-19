import json
import socket
from confluent_kafka import Consumer
from configuration import NSP_SERVER, KAFKA_KEYSTORE_PASSWORD


def start_kafka_consumer(topic, stop_event):
    conf = {
        "bootstrap.servers": f"{NSP_SERVER}:9193",
        "group.id": f"nsp-python-{socket.gethostname()}",
        "auto.offset.reset": "latest",

        "security.protocol": "SSL",
        "ssl.keystore.location": "nsp_keystore.p12",
        "ssl.keystore.password": KAFKA_KEYSTORE_PASSWORD,
        "ssl.ca.location": "ca.pem"
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])

    print("📡 Kafka consumer started")

    try:
        while not stop_event.is_set():
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print("❌ Kafka error:", msg.error())
                continue

            event = json.loads(msg.value().decode())
            print("📥 EVENT:", event)

    finally:
        consumer.close()
        print("🛑 Kafka consumer stopped")
