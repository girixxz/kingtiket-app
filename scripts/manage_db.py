from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import random
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

def add_user():
    print("\n== Tambah User Baru ==")
    username = input("Username: ")
    email = input("Email: ")
    whatsapp = input("Whatsapp: ")
    password = input("Password: ")
    role = input("Role (admin/user): ")

    user = {
        "username": username,
        "email": email,
        "whatsapp": whatsapp,
        "password": generate_password_hash(password),
        "role": role,
        "created_at": datetime.now()
    }
    db.users.insert_one(user)
    print("✅ User berhasil ditambahkan.\n")

def seed_dummy_data(total=5):
    print(f"\n== Menambahkan {total} data dummy ==")

    # Seed kategori
    categories = [
        {"name": "Konser", "description": "Konser musik dan hiburan"},
        {"name": "Seminar", "description": "Seminar dan workshop edukatif"},
        {"name": "Travel", "description": "Paket wisata dan travel"},
        {"name": "Olahraga", "description": "Event olahraga dan kompetisi"},
        {"name": "Festival", "description": "Festival budaya dan seni"},
    ]
    db.categories.delete_many({})
    for cat in categories:
        cat["created_at"] = datetime.now()
    db.categories.insert_many(categories)
    print("✅ Dummy kategori berhasil ditambahkan.")

    # Seed tiket
    tickets = []
    for i in range(total):
        tgl = datetime.now() + timedelta(days=random.randint(10, 60))
        tickets.append({
            "title": f"Event Dummy #{i+1}",
            "category": random.choice(categories)["name"],
            "price": random.randint(50000, 500000),
            "stock": random.randint(20, 200),
            "date": tgl,
            "location": f"Lokasi Dummy #{i+1}",
            "description": "Deskripsi event dummy",
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "status": "active",
            "created_at": datetime.now()
        })
    db.tickets.delete_many({})
    db.tickets.insert_many(tickets)
    print("✅ Dummy tiket berhasil ditambahkan.")

    # Seed orders
    db.orders.delete_many({})
    orders = []
    users = list(db.users.find())
    tickets_from_db = list(db.tickets.find())

    if not users:
        print("⚠️ Tidak ada user di database. Tambahkan user terlebih dahulu agar bisa membuat orders.\n")
        return

    for i in range(total):
        user = random.choice(users)
        ticket = random.choice(tickets_from_db)
        quantity = random.randint(1, 5)
        orders.append({
            "user_id": user["_id"],
            "ticket_id": ticket["_id"],
            "quantity": quantity,
            "total_price": ticket["price"] * quantity,
            "status": "paid",
            "created_at": datetime.now()
        })

    db.orders.insert_many(orders)
    print("✅ Dummy orders berhasil ditambahkan.\n")
    
def clear_users():
    konfirm = input("Apakah kamu yakin ingin menghapus SEMUA user? (yes/no): ")
    if konfirm.lower() == "yes":
        result = db.users.delete_many({})
        print(f"✅ {result.deleted_count} user telah dihapus.\n")
    else:
        print("❌ Operasi dibatalkan.\n")

def clear_dummy():
    db.tickets.delete_many({})
    db.categories.delete_many({})
    db.orders.delete_many({})
    print("✅ Semua data dummy (tickets, categories, orders) berhasil dihapus.\n")

def main():
    while True:
        print("""
======== KingTiket Data Manager ========

1. Tambah User
2. Tambah Data Dummy
3. Hapus Semua User
4. Hapus Data Dummy
0. Keluar
""")
        pilihan = input("Pilih menu [0-4]: ")

        if pilihan == "1":
            add_user()
        elif pilihan == "2":
            jumlah = input("Berapa data dummy tiket yang ingin ditambahkan? (default: 5): ")
            jumlah = int(jumlah) if jumlah.isdigit() else 5
            seed_dummy_data(jumlah)
        elif pilihan == "3":
            clear_users()
        elif pilihan == "4":
            clear_dummy()
        elif pilihan == "0":
            print("👋 Keluar dari program.")
            break
        else:
            print("❌ Pilihan tidak valid.\n")

if __name__ == "__main__":
    main()
