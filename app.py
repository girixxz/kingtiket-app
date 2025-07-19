from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader
import cloudinary.api
import base64
import qrcode
from io import BytesIO
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.get_default_database()

# Cloudinary setup
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


# Collections
users = db.users
tickets = db.tickets
categories = db.categories
orders = db.orders

@app.route('/')
def home():
    # Get trending tickets (limit 6)
    trending_tickets = list(tickets.find({"status": "active"}).limit(6))
    return render_template('home.html', tickets=trending_tickets)

@app.route('/cari-tiket')
def cari_tiket():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    date = request.args.get('date', '')
    
    query = {"status": "active"}
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    if category:
        query["category"] = category
    if date:
        query["date"] = {"$gte": datetime.strptime(date, "%Y-%m-%d")}
    
    ticket_list = list(tickets.find(query))
    categories_list = list(categories.find())
    
    return render_template('cari_tiket.html', 
                         tickets=ticket_list, 
                         categories=categories_list,
                         search=search,
                         selected_category=category,
                         selected_date=date)

@app.route('/tiket/<ticket_id>')
def detail_tiket(ticket_id):
    ticket = tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        flash('Tiket tidak ditemukan', 'error')
        return redirect(url_for('cari_tiket'))
    return render_template('detail_tiket.html', ticket=ticket)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users.find_one({"$or": [{"email": email}, {"username": email}]})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            
            if user.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Email/Username atau password salah', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        whatsapp = request.form['whatsapp']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Password tidak cocok', 'error')
            return render_template('register.html')
        
        if users.find_one({"$or": [{"email": email}, {"username": username}]}):
            flash('Email atau username sudah terdaftar', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        users.insert_one({
            "username": username,
            "email": email,
            "whatsapp": whatsapp,
            "password": hashed_password,
            "role": "user",
            "created_at": datetime.now()
        })
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/beli-tiket/<ticket_id>', methods=['POST'])
def beli_tiket(ticket_id):
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    quantity = int(request.form['quantity'])
    ticket = tickets.find_one({"_id": ObjectId(ticket_id)})
    
    if not ticket or ticket['stock'] < quantity:
        return jsonify({"error": "Stok tidak mencukupi"}), 400
    
    total_amount = ticket['price'] * quantity
    
    # Create order
    order_id = orders.insert_one({
        "user_id": ObjectId(session['user_id']),
        "ticket_id": ObjectId(ticket_id),
        "quantity": quantity,
        "total_amount": total_amount,
        "status": "pending",
        "created_at": datetime.now(),
        "payment_deadline": datetime.now() + timedelta(hours=24)
    }).inserted_id
    
    # Update ticket stock
    tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$inc": {"stock": -quantity}}
    )
    
    return redirect(url_for('pembayaran', order_id=str(order_id)))

@app.route('/pembayaran/<order_id>')
def pembayaran(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    order = orders.find_one({"_id": ObjectId(order_id), "user_id": ObjectId(session['user_id'])})
    if not order:
        flash('Pesanan tidak ditemukan', 'error')
        return redirect(url_for('home'))
    
    ticket = tickets.find_one({"_id": order['ticket_id']})
    
    # Generate QR Code
    qr_data = f"INV-{order_id[:8].upper()}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('pembayaran.html', 
                         order=order, 
                         ticket=ticket, 
                         qr_code=qr_code_base64,
                         invoice_id=qr_data)

@app.route('/konfirmasi-pembayaran/<order_id>', methods=['POST'])
def konfirmasi_pembayaran(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    orders.update_one(
        {"_id": ObjectId(order_id), "user_id": ObjectId(session['user_id'])},
        {"$set": {"status": "lunas", "paid_at": datetime.now()}}
    )
    
    flash('Pembayaran berhasil dikonfirmasi!', 'success')
    return redirect(url_for('riwayat_pemesanan'))

@app.route('/riwayat-pemesanan')
def riwayat_pemesanan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_orders = list(orders.find({"user_id": ObjectId(session['user_id'])}).sort("created_at", -1))
    
    # Get ticket details for each order
    for order in user_orders:
        order['ticket'] = tickets.find_one({"_id": order['ticket_id']})
    
    return render_template('riwayat_pemesanan.html', orders=user_orders)

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    total_tickets = tickets.count_documents({})
    total_orders = orders.count_documents({})
    total_revenue = sum([order['total_amount'] for order in orders.find({"status": "lunas"})])
    
    return render_template('admin/dashboard.html',
                         total_tickets=total_tickets,
                         total_orders=total_orders,
                         total_revenue=total_revenue)

@app.route('/admin/kategori')
def admin_kategori():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    categories_list = list(categories.find())
    return render_template('admin/kategori.html', categories=categories_list)

@app.route('/admin/kategori/add', methods=['POST'])
def admin_add_kategori():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    name = request.form['name']
    description = request.form['description']
    
    categories.insert_one({
        "name": name,
        "description": description,
        "created_at": datetime.now()
    })
    
    flash('Kategori berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_kategori'))

@app.route('/admin/kategori/delete/<kategori_id>')
def admin_delete_kategori(kategori_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    categories.delete_one({"_id": ObjectId(kategori_id)})
    flash('Kategori berhasil dihapus!', 'success')
    return redirect(url_for('admin_kategori'))

@app.route('/admin/tiket')
def admin_tiket():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    tickets_list = list(tickets.find())
    categories_list = list(categories.find())
    return render_template('admin/tiket.html', tickets=tickets_list, categories=categories_list)

@app.route('/admin/tiket/add', methods=['POST'])
def admin_add_tiket():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    title = request.form['title']
    category = request.form['category']
    price = int(request.form['price'])
    stock = int(request.form['stock'])
    date = datetime.strptime(request.form['date'], '%Y-%m-%d')
    location = request.form['location']
    description = request.form['description']
    
    # Handle image upload
    image_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"  # Default image
    
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder="kingtiket/tickets",
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto'}
                ]
            )
            image_url = upload_result['secure_url']
        except Exception as e:
            flash(f'Error uploading image: {str(e)}', 'error')
            return redirect(url_for('admin_tiket'))
    
    tickets.insert_one({
        "title": title,
        "category": category,
        "price": price,
        "stock": stock,
        "date": date,
        "location": location,
        "description": description,
        "image_url": image_url,
        "status": "active",
        "created_at": datetime.now()
    })
    
    flash('Tiket berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_tiket'))

@app.route('/admin/pemesanan')
def admin_pemesanan():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    status_filter = request.args.get('status', '')
    query = {}
    if status_filter:
        query['status'] = status_filter
    
    orders_list = list(orders.find(query).sort("created_at", -1))
    
    # Get user and ticket details for each order
    for order in orders_list:
        order['user'] = users.find_one({"_id": order['user_id']})
        order['ticket'] = tickets.find_one({"_id": order['ticket_id']})
    
    return render_template('admin/pemesanan.html', orders=orders_list, status_filter=status_filter)

@app.route('/admin/tiket/edit/<ticket_id>', methods=['POST'])
def admin_edit_tiket(ticket_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    title = request.form['title']
    category = request.form['category']
    price = int(request.form['price'])
    stock = int(request.form['stock'])
    date = datetime.strptime(request.form['date'], '%Y-%m-%d')
    location = request.form['location']
    description = request.form['description']
    
    # Handle image upload
    image_url = request.form.get('current_image_url')  # Keep existing image by default
    
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder="kingtiket/tickets",
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto'}
                ]
            )
            image_url = upload_result['secure_url']
        except Exception as e:
            flash(f'Error uploading image: {str(e)}', 'error')
            return redirect(url_for('admin_tiket'))
    
    tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": {
            "title": title,
            "category": category,
            "price": price,
            "stock": stock,
            "date": date,
            "location": location,
            "description": description,
            "image_url": image_url,
            "updated_at": datetime.now()
        }}
    )
    
    flash('Tiket berhasil diperbarui!', 'success')
    return redirect(url_for('admin_tiket'))

@app.route('/admin/tiket/delete/<ticket_id>')
def admin_delete_tiket(ticket_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    tickets.delete_one({"_id": ObjectId(ticket_id)})
    flash('Tiket berhasil dihapus!', 'success')
    return redirect(url_for('admin_tiket'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)