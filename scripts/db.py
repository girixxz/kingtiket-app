from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv


# Load .env
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.get_default_database()

# Clear existing data
db.categories.delete_many({})
db.tickets.delete_many({})
db.users.delete_many({})

# Seed categories
categories_data = [
    {"name": "Konser", "description": "Konser musik dan hiburan", "created_at": datetime.now()},
    {"name": "Seminar", "description": "Seminar dan workshop edukatif", "created_at": datetime.now()},
    {"name": "Travel", "description": "Paket wisata dan travel", "created_at": datetime.now()},
    {"name": "Olahraga", "description": "Event olahraga dan kompetisi", "created_at": datetime.now()},
    {"name": "Festival", "description": "Festival budaya dan seni", "created_at": datetime.now()}
]

db.categories.insert_many(categories_data)

# Seed tickets
tickets_data = [
    {
        "title": "Konser Raisa Live in Jakarta",
        "category": "Konser",
        "price": 250000,
        "stock": 150,
        "date": datetime.now() + timedelta(days=30),
        "location": "Jakarta Convention Center",
        "description": "Konser spektakuler Raisa dengan lagu-lagu terbaiknya",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "title": "Seminar Digital Marketing 2024",
        "category": "Seminar",
        "price": 150000,
        "stock": 80,
        "date": datetime.now() + timedelta(days=15),
        "location": "Hotel Mulia, Jakarta",
        "description": "Pelajari strategi digital marketing terkini dari para ahli",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "title": "Trip Bali 3D2N All Inclusive",
        "category": "Travel",
        "price": 1500000,
        "stock": 25,
        "date": datetime.now() + timedelta(days=45),
        "location": "Bali, Indonesia",
        "description": "Paket wisata Bali lengkap dengan hotel dan transportasi",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "title": "Jakarta Marathon 2024",
        "category": "Olahraga",
        "price": 200000,
        "stock": 500,
        "date": datetime.now() + timedelta(days=60),
        "location": "Monas, Jakarta",
        "description": "Ikuti marathon terbesar di Jakarta",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "title": "Festival Budaya Nusantara",
        "category": "Festival",
        "price": 75000,
        "stock": 300,
        "date": datetime.now() + timedelta(days=20),
        "location": "Taman Mini Indonesia Indah",
        "description": "Festival budaya dengan pertunjukan dari seluruh Indonesia",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "title": "Workshop Photography",
        "category": "Seminar",
        "price": 300000,
        "stock": 30,
        "date": datetime.now() + timedelta(days=25),
        "location": "Studio Foto Jakarta",
        "description": "Belajar teknik fotografi dari fotografer profesional",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        "status": "active",
        "created_at": datetime.now()
    }
]

db.tickets.insert_many(tickets_data)

# Create admin user
from werkzeug.security import generate_password_hash

admin_user = {
    "username": "admin",
    "email": "admin@kingtiket.pro",
    "whatsapp": "081234567890",
    "password": generate_password_hash("admin123"),
    "role": "admin",
    "created_at": datetime.now()
}

db.users.insert_one(admin_user)

print("Database seeded successfully!")
print("Admin credentials:")
print("Email: admin@kingtiket.pro")
print("Password: admin123")
