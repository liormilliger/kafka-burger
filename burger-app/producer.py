import sys
import os
import random
import json
import time
from datetime import datetime
from kafka import KafkaProducer

# Add the parent directory to the system path to allow importing from 'shared'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.menu import MENU # This line should now work

# Load Haifa streets list
with open("data/haifa_streets.txt", "r") as f:
    streets = [line.strip() for line in f.readlines()]

# Sample list of first and last names for random customers
FIRST_NAMES = ["David", "Maya", "Eli", "Sara", "Noam", "Yael", "Itai", "Roni"]
LAST_NAMES = ["Levi", "Cohen", "Peretz", "Barak", "Shapiro", "Goldberg", "Klein", "Azar"]

def random_full_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_order(menu, streets):
    # Burger options (flattened)
    burger_options = []
    for weight, sizes in menu['Burger'].items():
        for size, price in sizes.items():
            burger_options.append((f"{weight} {size}", price))
    burger_choice, burger_price = random.choice(burger_options)

    # Toppings (zero or more)
    topping_options = list(menu['Toppings'].items())
    num_toppings = random.randint(0, len(topping_options))
    toppings_chosen = random.sample(topping_options, num_toppings)
    toppings_price = sum(price for _, price in toppings_chosen)

    # Side (zero or one)
    side_options = list(menu['Sides'].items())
    side_chosen = random.choice(side_options + [(None, 0)])
    side_name, side_price = side_chosen

    # Drink (zero or one)
    drink_options = list(menu['Drinks'].items())
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
    # If running inside a Docker container on the same network, 'kafka:9094' or 'kafka:9092'
    # If running on the host machine but Kafka is in Docker, 'localhost:9092'
    # If connecting from another machine, it would be 'EC2_PUBLIC_IP:9092'
    # For now, let's assume it's run on the EC2 host and connecting to the Docker-mapped port
    # Or, if producer itself will be a docker container, then it would be 'kafka:9092'
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    topic = "orders" # Consider renaming this topic based on your architecture (e.g., "order_received_events")
    print("Starting order producer. Press Ctrl+C to exit.")
    print(f"Connecting to Kafka at: {kafka_bootstrap_servers}")
    try:
        while True:
            order = generate_random_order(MENU, streets)
            producer.send(topic, order)
            print(f"Produced order: {order}")
            time.sleep(3)  # wait 3 seconds before next order
    except KeyboardInterrupt:
        print("Producer stopped.")
    finally:
        producer.close() # Ensure producer is closed gracefully

if __name__ == "__main__":
    main()