import sys
import os
import random
import json
import time
from datetime import datetime
from kafka import KafkaProducer

# --- PATH ADJUSTMENT FOR IMPORTS ---
# Add the parent directory (burger-app) to the system path
# This allows importing from 'shared' and 'data' correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- END PATH ADJUSTMENT ---

from shared.menu import MENU

# Load Haifa streets list
# Ensure 'data' directory is correctly located relative to burger-app root
# or adjust path if necessary. Current setup assumes burger-app/data/haifa_streets.txt
with open("data/haifa_streets.txt", "r") as f:
    streets = [line.strip() for line in f.readlines()]

# Sample list of first and last names for random customers
FIRST_NAMES = ["David", "Maya", "Eli", "Sara", "Noam", "Yael", "Itai", "Roni"]
LAST_NAMES = ["Levi", "Cohen", "Peretz", "Barak", "Shapiro", "Goldberg", "Klein", "Azar"]

def random_full_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_order(menu, streets):
    # Burger options
    # The burger menu is already flattened, so we can directly pick an item
    burger_options = list(menu['Burger'].items()) # Get list of (name, price) tuples
    burger_choice_tuple = random.choice(burger_options)
    burger_choice = burger_choice_tuple[0] # e.g., "160g_single"
    burger_price = burger_choice_tuple[1]  # e.g., 45

    # Toppings (zero or more)
    topping_options = list(menu['Toppings'].items())
    num_toppings = random.randint(0, len(topping_options))
    toppings_chosen = random.sample(topping_options, num_toppings)
    toppings_price = sum(price for _, price in toppings_chosen)

    # Side (zero or one)
    side_options = list(menu['Sides'].items())
    # Add an option for no side (None, 0 price)
    side_chosen = random.choice(side_options + [(None, 0)])
    side_name, side_price = side_chosen

    # Drink (zero or one)
    drink_options = list(menu['Drinks'].items())
    # Add an option for no drink (None, 0 price)
    drink_chosen = random.choice(drink_options + [(None, 0)])
    drink_name, drink_price = drink_chosen

    total_price = burger_price + toppings_price + side_price + drink_price

    street = random.choice(streets)
    house_number = random.randint(1, 100)
    customer_address = f"{street} {house_number}, Haifa"

    order_content = {
        "Burger": burger_choice,
        "Toppings": [name for name, _ in toppings_chosen],
        "Side": side_name,
        "Drink": drink_name,
        "Prices": {
            "Burger": burger_price,
            "Toppings": toppings_price,
            "Side": side_price,
            "Drink": drink_price
        }
    }

    order = {
        "FullName": random_full_name(),
        "OrderContent": order_content,
        "TotalPrice": total_price,
        "CustomerAddress": customer_address,
        "OrderTimestamp": datetime.utcnow().isoformat() + "Z"
    }

    return order

def main():
    # Determine bootstrap_servers based on environment
    # If running on the EC2 host directly, 'localhost:9092' connects to the Docker-mapped port.
    # If running as a Docker container on the same network, 'kafka:9092' (internal Docker DNS).
    # If connecting from a different machine, use the EC2_PUBLIC_IP.
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    topic = "orders" # This is the topic where orders will be published
    print("Starting order producer. Press Ctrl+C to exit.")
    print(f"Connecting to Kafka at: {kafka_bootstrap_servers}")
    try:
        while True:
            order = generate_random_order(MENU, streets)
            producer.send(topic, value=order) # Use 'value=' for clarity, though optional
            print(f"Produced order: {order}")
            time.sleep(3)  # wait 3 seconds before next order
    except KeyboardInterrupt:
        print("Producer stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if producer:
            producer.close() # Ensure producer is closed gracefully

if __name__ == "__main__":
    main()