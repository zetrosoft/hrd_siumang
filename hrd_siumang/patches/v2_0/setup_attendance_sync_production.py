import frappe
from hrd_siumang.utils.attendance_utils import process_auto_attendance

def execute():
    # 1. Tambahkan Database Index jika belum ada
    # Ini mempercepat query 'WHERE attendance IS NULL' saat data check-in sudah jutaan baris
    try:
        frappe.db.sql("""
            ALTER TABLE `tabEmployee Checkin` 
            ADD INDEX IF NOT EXISTS `idx_attendance_status` (`attendance`)
        """)
    except Exception:
        pass

    # 2. Jalankan Pemicu Sinkronisasi Attendance untuk seluruh data lama
    # Ini akan memproses data yang baru saja diimpor ke server produksi
    print("Memulai sinkronisasi Attendance otomatis...")
    process_auto_attendance()
    print("Sinkronisasi selesai.")
