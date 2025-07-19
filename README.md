# 🎫 KingTiket.Pro - Aplikasi Pemesanan Tiket Online

**KingTiket.Pro** adalah aplikasi pemesanan tiket berbasis web yang memungkinkan pengguna untuk mendaftar, login, melihat daftar tiket berdasarkan kategori, melakukan pemesanan, melihat riwayat, dan mengunduh tiket dalam format PDF. Aplikasi ini dibangun menggunakan **Flask**, **MongoDB**, dan **Cloudinary**.

---

## 🚀 Fitur Utama

### 👤 Autentikasi Pengguna
- Register & Login
- Role pengguna: user & admin

### 📦 Manajemen Tiket
- Admin dapat menambahkan, mengedit, dan menghapus:
  - Kategori tiket
  - Tiket (nama, harga, gambar, stok)

### 🎫 Pemesanan Tiket
- Pengguna dapat memilih tiket berdasarkan kategori
- Melihat detail tiket
- Memesan tiket dengan jumlah tertentu

### 💳 Pembayaran
- Tagihan ditampilkan setelah pemesanan
- Status pemesanan: pending / lunas

### 📄 Riwayat & PDF
- Riwayat pemesanan pengguna tersedia
- Tiket dapat diunduh dalam format PDF (jika status = lunas)

### ☁️ Penyimpanan Gambar
- Upload dan pengelolaan gambar tiket menggunakan **Cloudinary**

---

## 🛠️ Teknologi yang Digunakan

- Python 3.x
- Flask
- MongoDB (via PyMongo)
- Cloudinary
- ReportLab (untuk generate PDF)
- Flask-CORS

---

## ⚙️ Cara Menjalankan Proyek Ini

### 1. Clone repository
```bash
git clone https://github.com/username/kingtiket.git
cd kingtiket
```