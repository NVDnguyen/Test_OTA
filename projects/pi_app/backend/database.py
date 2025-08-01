# backend/database.py
from pymongo import MongoClient, ASCENDING, collection
from .config import settings
import random
import os

# --- Database Connection ---
# This setup creates a single client that can be shared across the application.
# PyMongo's client is thread-safe and includes connection pooling.
client = MongoClient(settings.MONGO_URI)
db = client["shopping_cart_db"]

# --- Collection Getters (for Dependency Injection) ---
def get_products_collection() -> collection.Collection:
    return db["products"]

def get_users_collection() -> collection.Collection:
    return db["users"]

def get_orders_collection() -> collection.Collection:
    return db["order_history"]

def get_map_collection() -> collection.Collection:
    return db["map"]

# --- Database Helpers ---
def ensure_indexes():
    """Creates unique indexes for collections if they don't exist."""
    get_products_collection().create_index([("id", ASCENDING)], unique=True)
    get_users_collection().create_index([("email", ASCENDING)], unique=True)
    print("Database indexes ensured.")

PRODUCT_NAMES = [
    "Apple", "Banana", "Orange", "Milk", "Bread", "Eggs", "Cheese", "Chicken", "Rice", "Pasta",
    "Tomato", "Potato", "Onion", "Carrot", "Cucumber", "Lettuce", "Yogurt", "Butter", "Juice", "Coffee"
]
SUBTITLES = ["Fresh", "Organic", "Imported", "Local", "Premium", "Budget"]
UNITS = ["each", "kg", "pack", "bottle", "box"]
random.seed(42)

def random_location():
    return {"x": random.randint(30, 470), "y": random.randint(30, 470)}

def generate_products(n=20):
    products = []
    # Add original demo products with locations
    demo_products = [
        {'id': 1, 'name': 'Fifa 19', 'subtitle': 'PS4', 'price': 1500000, 'currency': 'VND', 'quantity': 1, 'unit': 'pack', 'product_img_url': 'https://via.placeholder.com/80/cccccc/000000?Text=Game', 'location': [{"x": 100, "y": 100}]},
        {'id': 2, 'name': 'Glacier White 500GB', 'subtitle': 'PS4', 'price': 8000000, 'currency': 'VND', 'quantity': 1, 'unit': 'each', 'product_img_url': 'https://via.placeholder.com/80/f0f0f0/000000?Text=Console', 'location': [{"x": 200, "y": 200}]},
        {'id': 3, 'name': 'Platinum Headset', 'subtitle': 'PS4', 'price': 2500000, 'currency': 'VND', 'quantity': 1, 'unit': 'each', 'product_img_url': 'https://via.placeholder.com/80/e0e0e0/000000?Text=Accessory', 'location': [{"x": 300, "y": 300}]},
    ]
    products.extend(demo_products)
    # Add random mock products
    for i in range(n):
        name = PRODUCT_NAMES[i % len(PRODUCT_NAMES)] + f" {i+1}"
        product = {
            "id": i+100,
            "name": name,
            "subtitle": random.choice(SUBTITLES),
            "price": random.randint(10000, 2000000),  # VND price range
            "currency": "VND",
            "quantity": random.randint(1, 50),
            "unit": random.choice(UNITS),
            "product_img_url": "https://via.placeholder.com/80/cccccc/000000?Text=Product",
            "location": [random_location() for _ in range(random.randint(1, 3))]
        }
        products.append(product)
    return products

def seed_database_if_empty():
    """Clears and reseeds the products and map collections with initial data, only in development."""
    if getattr(settings, "APP_ENV", "development") != "development":
        print("Skipping database seeding: not in development environment.")
        return
    products_collection = get_products_collection()
    map_collection = get_map_collection()
    # Always ensure text index exists
    products_collection.create_index([("name", "text")])

    # Clear collections before reseeding
    products_collection.delete_many({})
    map_collection.delete_many({})

    # Reseed products
    initial_products = generate_products(20)
    print("Seeding database with mock products...")
    products_collection.insert_many(initial_products)
    print("Database seeded.")

    # Seed default_map.png
    default_map_path = os.path.join(os.path.dirname(__file__), "default_map.png")
    with open(default_map_path, "rb") as f:
        image_bytes = f.read()
    map_doc = {"name": "mall_map", "image": image_bytes, "content_type": "image/png"}
    map_collection.insert_one(map_doc)
    print("Seeded mall map image from default_map.png.")