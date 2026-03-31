import frappe
import json
from frappe.utils import getdate, nowdate, add_days, get_time, logger

def process_auto_attendance():
    """
    Fungsi kustom Production-Ready untuk memproses Employee Checkin menjadi Attendance.
    Logika: Mengikuti aturan Shift, mencatat Late Entry/Early Exit, 
    dan menangani error per-record agar tidak menghentikan seluruh proses.
    """
    yesterday = add_days(nowdate(), -1)
    log = logger("attendance_sync")
    
    # Ambil data check-in per karyawan per hari yang belum diproses
    try:
        checkins = frappe.db.sql("""
            SELECT 
                employee, 
                DATE(time) as attendance_date,
                MIN(time) as in_time,
                MAX(time) as out_time
            FROM `tabEmployee Checkin`
            WHERE (attendance IS NULL OR attendance = '')
            AND DATE(time) <= %s
            GROUP BY employee, DATE(time)
        """, (yesterday,), as_dict=True)
    except Exception as e:
        log.error(f"Gagal mengambil data check-in: {str(e)}")
        return

    if not checkins:
        return

    processed_count = 0
    error_count = 0

    for entry in checkins:
        try:
            # 1. Cari Shift Assignment yang aktif
            shift_assignment = frappe.db.sql("""
                SELECT shift_type FROM `tabShift Assignment`
                WHERE employee = %s AND start_date <= %s 
                AND (end_date IS NULL OR end_date >= %s)
                AND docstatus = 1 LIMIT 1
            """, (entry.employee, entry.attendance_date, entry.attendance_date), as_dict=True)

            shift_type = None
            if shift_assignment:
                shift_type = frappe.get_doc("Shift Type", shift_assignment[0].shift_type)

            late_entry = 0
            early_exit = 0
            remarks = []

            if shift_type:
                # Hitung Keterlambatan
                shift_start = get_time(shift_type.start_time)
                actual_in = get_time(entry.in_time)
                grace_in = getattr(shift_type, "late_entry_grace_period", 0)
                
                if actual_in > shift_start:
                    diff_in = (actual_in.hour * 3600 + actual_in.minute * 60) - (shift_start.hour * 3600 + shift_start.minute * 60)
                    if diff_in > (grace_in * 60):
                        late_entry = 1
                        remarks.append(f"Terlambat {diff_in // 60} mnt")

                # Hitung Pulang Cepat
                shift_end = get_time(shift_type.end_time)
                grace_out = getattr(shift_type, "early_exit_grace_period", 0)
                
                if entry.in_time != entry.out_time:
                    actual_out = get_time(entry.out_time)
                    if actual_out < shift_end:
                        diff_out = (shift_end.hour * 3600 + shift_end_time.minute * 60) - (actual_out.hour * 3600 + actual_out.minute * 60)
                        if diff_out > (grace_out * 60):
                            early_exit = 1
                            remarks.append(f"Pulang Cepat {diff_out // 60} mnt")
                else:
                    early_exit = 1
                    remarks.append("Tidak ada scan OUT")

            # 2. Buat/Update Attendance
            existing = frappe.db.get_value("Attendance", {
                "employee": entry.employee,
                "attendance_date": entry.attendance_date,
                "docstatus": ["!=", 2]
            })

            comment_str = "; ".join(remarks) if remarks else ""
            
            if existing:
                doc = frappe.get_doc("Attendance", existing)
                doc.db_set("in_time", entry.in_time)
                if entry.in_time != entry.out_time:
                    doc.db_set("out_time", entry.out_time)
                doc.db_set("late_entry", late_entry)
                doc.db_set("early_exit", early_exit)
                doc.db_set("status", "Present")
            else:
                doc = frappe.new_doc("Attendance")
                doc.employee = entry.employee
                doc.attendance_date = entry.attendance_date
                doc.in_time = entry.in_time
                if entry.in_time != entry.out_time:
                    doc.out_time = entry.out_time
                if shift_type: doc.shift = shift_type.name
                doc.status = "Present"
                doc.late_entry = late_entry
                doc.early_exit = early_exit
                doc.insert(ignore_permissions=True)
                doc.submit()

            # 3. Hubungkan Check-in
            attendance_name = existing or doc.name
            frappe.db.sql("UPDATE `tabEmployee Checkin` SET attendance = %s WHERE employee = %s AND DATE(time) = %s", 
                         (attendance_name, entry.employee, entry.attendance_date))
            
            if comment_str and not existing:
                doc.add_comment("Comment", comment_str)
            
            processed_count += 1
            if processed_count % 50 == 0:
                frappe.db.commit() # Commit setiap 50 record untuk keamanan memori

        except Exception as e:
            error_count += 1
            log.error(f"Error processing {entry.employee} on {entry.attendance_date}: {str(e)}")
            continue

    frappe.db.commit()
    log.info(f"Sync Selesai. Sukses: {processed_count}, Gagal: {error_count}")
