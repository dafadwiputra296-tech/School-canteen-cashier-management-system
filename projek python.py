import mysql.connector
import getpass
from datetime import datetime

# == Koneksi Database ==
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # isi password MySQL kalau ada
        database="canteen_db"
    )

# == Registrasi Akun Baru ==
def register(db):
    cursor = db.cursor()

    print("\n== REGISTRASI AKUN BARU ==")
    username = input("Buat username: ")
    password = getpass.getpass("Buat password: ")
    role = input("Pilih role (admin/kasir): ")

    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                       (username, password, role))
        db.commit()
        print("Akun berhasil dibuat!")
    except mysql.connector.Error as e:
        print("Gagal registrasi:", e)

# == Login ==
def login(db):
    cursor = db.cursor(dictionary=True)

    print("\n== LOGIN ==")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                   (username, password))
    user = cursor.fetchone()

    if user:
        print(f"Login berhasil sebagai {user['role']}")
        return user
    else:
        print("Username atau password salah!")
        return None

# == Fungsi Produk ==
def lihat_produk(db, show_inactive=False):
    cursor = db.cursor()
    if show_inactive:
        cursor.execute("SELECT * FROM products")
    else:
        cursor.execute("SELECT * FROM products WHERE is_active=1")
    rows = cursor.fetchall()

    print("\n== DAFTAR PRODUK ==")
    for row in rows:
        status = "Aktif" if row[4]==1 else "Nonaktif"
        print(f"ID:{row[0]} | {row[1]} | Harga:{row[2]} | Stok:{row[3]} | Status:{status}")

def tambah_produk(db):
    cursor = db.cursor()

    nama = input("Nama produk: ")
    harga = float(input("Harga: "))
    stok = int(input("Stok: "))

    cursor.execute("INSERT INTO products (name, price, stock, is_active) VALUES (%s,%s,%s,1)",
                   (nama, harga, stok))
    db.commit()
    print("Produk berhasil ditambahkan!")

def update_produk(db):
    lihat_produk(db)
    cursor = db.cursor()
    pid = int(input("Masukkan ID produk yang mau diupdate (0 untuk batal): "))

    if pid == 0:
        print("Batal update produk.")
        return

    nama = input("Nama baru (kosongkan jika tidak diubah): ")
    harga = input("Harga baru (kosongkan jika tidak diubah): ")
    stok = input("Stok baru (kosongkan jika tidak diubah): ")

    query = "UPDATE products SET "
    values = []
    if nama:
        query += "name=%s,"
        values.append(nama)
    if harga:
        query += "price=%s,"
        values.append(float(harga))
    if stok:
        query += "stock=%s,"
        values.append(int(stok))
    query = query.rstrip(",") + " WHERE product_id=%s"
    values.append(pid)

    cursor.execute(query, tuple(values))
    db.commit()
    print("Produk berhasil diupdate!")

def hapus_produk(db):
    lihat_produk(db)
    cursor = db.cursor()
    pid = int(input("Masukkan ID produk yang mau dihapus: "))

    try:
        cursor.execute("UPDATE products SET is_active=0 WHERE product_id=%s", (pid,))
        db.commit()
        print("Produk berhasil dihapus (soft delete).")
    except mysql.connector.Error as e:
        print("Gagal hapus produk:", e)

# == Fungsi Aktifkan Ulang Produk ==
def aktifkan_produk(db):
    cursor = db.cursor()
    cursor.execute("SELECT product_id, name FROM products WHERE is_active=0")
    produk_nonaktif = cursor.fetchall()

    if not produk_nonaktif:
        print("\nTidak ada produk yang bisa diaktifkan ulang.")
        return

    print("\n== DAFTAR PRODUK NONAKTIF ==")
    for p in produk_nonaktif:
        print(f"ID: {p[0]} | {p[1]}")

    id_aktif = input("Masukkan ID produk yang ingin diaktifkan ulang (0 untuk batal): ")
    if id_aktif == "0":
        print("Batal mengaktifkan produk.")
        return

    cursor.execute("UPDATE products SET is_active=1 WHERE product_id=%s", (id_aktif,))
    db.commit()
    print("Produk berhasil diaktifkan ulang!")

# == Fungsi Transaksi ==
def buat_transaksi(db, user):
    lihat_produk(db)
    cursor = db.cursor()

    produk_id = int(input("Masukkan ID produk: "))
    qty = int(input("Jumlah beli: "))

    cursor.execute("SELECT price, stock FROM products WHERE product_id=%s AND is_active=1", (produk_id,))
    result = cursor.fetchone()

    if result:
        harga, stok = result
        if qty > stok:
            print("Stok tidak cukup!")
        else:
            subtotal = harga * qty
            cursor.execute("INSERT INTO transactions (user_id, total_amount) VALUES (%s, %s)",
                           (user['user_id'], subtotal))
            trans_id = cursor.lastrowid

            cursor.execute("INSERT INTO transaction_details (transaction_id, product_id, quantity, subtotal) VALUES (%s,%s,%s,%s)",
                           (trans_id, produk_id, qty, subtotal))

            cursor.execute("UPDATE products SET stock=stock-%s WHERE product_id=%s", (qty, produk_id))

            db.commit()
            print("Transaksi berhasil dibuat!")
    else:
        print("Produk tidak ditemukan!")

def laporan_transaksi(db):
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM transactions ORDER BY transaction_id DESC")
    rows = cursor.fetchall()

    print("\n== LAPORAN TRANSAKSI PENJUALAN ==")
    for row in rows:
        print(f"\nID Transaksi: {row['transaction_id']}")
        print(f"Kasir (User ID): {row['user_id']}")
        print(f"Tanggal: {row['transaction_date']}")
        print(f"Total: {row['total_amount']}")

        cursor.execute("SELECT p.name, td.quantity, td.subtotal FROM transaction_details td JOIN products p ON td.product_id=p.product_id WHERE td.transaction_id=%s",
                       (row['transaction_id'],))
        details = cursor.fetchall()
        for d in details:
            print(f" - {d['name']} x{d['quantity']} = {d['subtotal']}")

# == Menu Admin ==
def admin_menu(db):
    while True:
        print("\n== MENU ADMIN ==")
        print("1. Lihat Produk")
        print("2. Tambah Produk")
        print("3. Update Produk")
        print("4. Hapus Produk")
        print("5. Laporan Transaksi Penjualan")
        print("6. Aktifkan Ulang Produk")
        print("7. Logout")
        pilih = input("Pilih menu: ")

        if pilih == "1":
            lihat_produk(db)
        elif pilih == "2":
            tambah_produk(db)
        elif pilih == "3":
            update_produk(db)
        elif pilih == "4":
            hapus_produk(db)
        elif pilih == "5":
            laporan_transaksi(db)
        elif pilih == "6":
            aktifkan_produk(db)
        elif pilih == "7":
            break
        else:
            print("Pilihan tidak valid!")

# == Menu Kasir ==
def kasir_menu(db, user):
    while True:
        print("\n== MENU KASIR ==")
        print("1. Lihat Produk")
        print("2. Buat Transaksi")
        print("3. Laporan Transaksi Penjualan")
        print("4. Logout")
        pilih = input("Pilih menu: ")

        if pilih == "1":
            lihat_produk(db)
        elif pilih == "2":
            buat_transaksi(db, user)
        elif pilih == "3":
            laporan_transaksi(db)
        elif pilih == "4":
            break
        else:
            print("Pilihan tidak valid!")

# == Main Program ==
def main():
    db = connect_db()
    while True:
        print("\n== SISTEM KANTIN ==")
        print("1. Login")
        print("2. Registrasi akun baru")
        print("3. Keluar")
        pilih = input("Pilih menu: ")

        if pilih == "1":
            user = login(db)
            if user:
                if user['role'] == "admin":
                    admin_menu(db)
                else:
                    kasir_menu(db, user)
        elif pilih == "2":
            register(db)
        elif pilih == "3":
            print("Keluar...")
            break
        else:
            print("Pilihan tidak valid!")

    db.close()

if __name__ == "__main__":
    main()
