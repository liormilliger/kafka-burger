# producer.py
import json
import time
import random
from confluent_kafka import Producer, KafkaException

# Import menu and street names (assuming they are in the same directory or accessible via path)
# For a real project, you might structure this with a 'shared' module.
from shared.menu import MENU # Corrected import path for menu.py

# Load street names from the provided file
try:
    with open('haifa_streetnames.txt', 'r') as f:
        STREET_NAMES = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Error: haifa_streetnames.txt not found. Please ensure it's in the same directory.")
    STREET_NAMES = ["Default Street 1", "Default Street 2"] # Fallback

# Kafka configuration
KAFKA_BROKER = 'localhost:9092' # This matches your Docker Compose setup
TOPICS = ['order_status', 'kitchen', 'payment', 'inventory', 'delivery']

def get_random_menu_item():
    """Selects a random item from the MENU."""
    category = random.choice(list(MENU.keys()))
    item_name = random.choice(list(MENU[category].keys()))
    return category, item_name, MENU[category][item_name]

def generate_random_order():
    """Generates a random burger order with items from the menu."""
    order = {
        "order_id": str(random.randint(10000, 99999)),
        "timestamp": int(time.time()),
        "items": [],
        "total_price": 0,
        "delivery_address": random.choice(STREET_NAMES) + ", Haifa",
        "customer_info": {
            "name": f"Customer_{random.randint(1, 100)}",
            "phone": f"05{random.randint(0, 9)}{random.randint(1000000, 9999999)}"
        }
    }

    num_items = random.randint(1, 5) # Not more than 5 items in total
    current_item_count = 0

    # Ensure at least one burger if possible
    if "Burger" in MENU and random.random() < 0.8 and current_item_count < num_items: # 80% chance for a burger
        burger_type = random.choice(list(MENU["Burger"].keys()))
        order["items"].append({"category": "Burger", "name": burger_type, "price": MENU["Burger"][burger_type]})
        order["total_price"] += MENU["Burger"][burger_type]
        current_item_count += 1

    # Add other items up to the limit
    while current_item_count < num_items:
        category, item_name, item_price = get_random_menu_item()
        order["items"].append({"category": category, "name": item_name, "price": item_price})
        order["total_price"] += item_price
        current_item_count += 1

    return order

def delivery_report(err, msg):
    """Callback function for Kafka message delivery reports."""
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to topic '{msg.topic()}' [{msg.partition()}] at offset {msg.offset()}")

def send_order_to_kafka(producer, order):
    """Sends the generated order to various Kafka topics using confluent_kafka."""
    order_id = order["order_id"]
    print(f"--- Sending Order {order_id} ---")
    for topic in TOPICS:
        try:
            message_payload = {
                "order_id": order_id,
                "topic": topic, # Indicate which topic this specific message is for
                "payload": order
            }
            # Asynchronous produce with callback
            producer.produce(
                topic,
                key=order_id.encode('utf-8'), # Use order_id as key for consistent partitioning
                value=json.dumps(message_payload).encode('utf-8'),
                callback=delivery_report
            )
            # Poll for any delivered messages or errors
            producer.poll(0) # Non-blocking poll
        except KafkaException as e:
            print(f"Kafka error sending order {order_id} to topic {topic}: {e}")
        except Exception as e:
            print(f"General error sending order {order_id} to topic {topic}: {e}")
    # Ensure all outstanding messages are delivered
    producer.flush(timeout=30) # Flush with a timeout
    print(f"Order {order_id} sent successfully (or flushed with timeout).")

def main():
    """Main function to run the order producer."""
    producer = None
    try:
        conf = {'bootstrap.servers': KAFKA_BROKER}
        producer = Producer(conf)
        print(f"Kafka Producer connected to {KAFKA_BROKER}")

        while True:
            order = generate_random_order()
            send_order_to_kafka(producer, order)
            time.sleep(60) # Generate an order every minute

    except Exception as e:
        print(f"Failed to connect to Kafka or an error occurred: {e}")
    finally:
        if producer:
            # Ensure any remaining messages are delivered before exiting
            producer.flush()
            print("Kafka Producer closed and flushed.")

if __name__ == "__main__":
    main()
