import frappe

def execute():
    """
    Patch untuk membuat Leave Type secara otomatis saat migrasi.
    Sesuai rancangan HR Siumang.
    """
    leave_types = [
        {
            "leave_type_name": "Sakit (Bersurat)",
            "is_unpaid": 0,
            "include_holiday": 0,
            "allow_negative_balance": 0
        },
        {
            "leave_type_name": "Sakit (Tanpa Surat)",
            "is_unpaid": 1,
            "include_holiday": 0,
            "allow_negative_balance": 1 # Biarkan negatif agar bisa terpotong di payroll
        },
        {
            "leave_type_name": "Cuti Bersama",
            "is_unpaid": 0,
            "include_holiday": 0,
            "allow_negative_balance": 1 # Biarkan negatif agar logika payroll bisa mendeteksi jatah habis
        }
    ]

    for lt_data in leave_types:
        if not frappe.db.exists("Leave Type", lt_data["leave_type_name"]):
            lt = frappe.get_doc({
                "doctype": "Leave Type",
                **lt_data
            })
            lt.insert(ignore_permissions=True)
            print(f"Patch: Created Leave Type {lt_data['leave_type_name']}")
        else:
            # Update existing if needed
            frappe.db.set_value("Leave Type", lt_data["leave_type_name"], "is_unpaid", lt_data["is_unpaid"])
    
    frappe.db.commit()
