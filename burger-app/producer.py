import random
import json
import time
from datetime import datetime
from kafka import KafkaProducer
from shared.menu import MENU

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
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    topic = "orders"
    print("Starting order producer. Press Ctrl+C to exit.")
    try:
        while True:
            order = generate_random_order(MENU, streets)
            producer.send(topic, order)
            print(f"Produced order: {order}")
            time.sleep(3)  # wait 3 seconds before next order
    except KeyboardInterrupt:
        print("Producer stopped.")

if __name__ == "__main__":
    main()
