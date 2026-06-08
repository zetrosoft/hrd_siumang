import math
import frappe
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
from frappe import _

@frappe.whitelist()
def get_payroll_denominator_info(employee):
    """
    Mengembalikan informasi denominator sistem, status shift, 
    nama shift, dan holiday list karyawan.
    Digunakan untuk auto-fill dan transparansi di UI.
    """
    try:
        # Cari Shift Assignment aktif
        shift_assignment = frappe.get_value("Shift Assignment", 
            {"employee": employee, "docstatus": 1, "status": "Active"}, 
            "shift_type")
        
        source = "Shift Assignment"
        if not shift_assignment:
            shift_assignment = frappe.get_value("Employee", employee, "default_shift")
            source = "Default Shift"
            
        if not shift_assignment:
            return {"has_shift": False, "denominator": 25, "shift": None, "holiday_list": None}
            
        holiday_list = frappe.get_value("Shift Type", shift_assignment, "holiday_list")
        if not holiday_list:
            holiday_list = frappe.get_value("Employee", employee, "holiday_list")
            
        if not holiday_list:
            return {
                "has_shift": True, 
                "denominator": 25, 
                "shift": shift_assignment, 
                "holiday_list": "Tidak Ditemukan",
                "source": source
            }
            
        holidays = frappe.get_all("Holiday", 
            filters={"parent": holiday_list, "weekly_off": 1}, 
            fields=["holiday_date"], 
            limit=14)
            
        if not holidays:
            return {
                "has_shift": True, 
                "denominator": 25, 
                "shift": shift_assignment, 
                "holiday_list": holiday_list,
                "source": source
            }
            
        unique_days = set()
        for h in holidays:
            unique_days.add(h.holiday_date.weekday())
            
        denominator = 21 if len(unique_days) >= 2 else 25
        return {
            "has_shift": True, 
            "denominator": denominator, 
            "shift": shift_assignment, 
            "holiday_list": holiday_list,
            "source": source
        }
            
    except Exception:
        return {"has_shift": False, "denominator": 25}

@frappe.whitelist()
def get_payroll_denominator(employee):
    """
    Menentukan pembagi (denominator) gaji.
    1. Cek Manual Override di Employee Allowance Data
    2. Jika tidak ada, hitung otomatis berdasarkan Shift/Holiday List
    """
    try:
        # 1. Cek Manual Override
        manual_val = frappe.db.get_value("Employee Allowance Data", 
            {"employee": employee}, "manual_payroll_denominator")
        
        if manual_val and manual_val > 0:
            return manual_val

        # 2. Cari Shift Assignment aktif
        shift_assignment = frappe.get_value("Shift Assignment", 
            {"employee": employee, "docstatus": 1, "status": "Active"}, 
            "shift_type")
        
        if not shift_assignment:
            # Jika tidak ada shift assignment, coba ambil dari Default Shift di Employee
            shift_assignment = frappe.get_value("Employee", employee, "default_shift")
            
        if not shift_assignment:
            return 25 # Default jika tidak ada shift terdeteksi
            
        # 2. Ambil Holiday List dari Shift Type
        holiday_list = frappe.get_value("Shift Type", shift_assignment, "holiday_list")
        
        if not holiday_list:
            # Jika shift type tidak ada holiday list, ambil dari Employee
            holiday_list = frappe.get_value("Employee", employee, "holiday_list")
            
        if not holiday_list:
            return 25
            
        # 3. Hitung jumlah Weekly Off (Hari Libur Mingguan)
        # Frappe menyimpan weekly off di tabel child Holiday
        weekly_offs = frappe.db.count("Holiday", {
            "parent": holiday_list,
            "weekly_off": 1
        })
        
        # Logika: 
        # Jika hari libur mingguan >= 8 (Sabtu & Minggu dalam sebulan), asumsikan 5 hari kerja -> 21
        # Jika hari libur mingguan < 8 (Hanya Minggu), asumsikan 6 hari kerja -> 25
        # Catatan: Kita gunakan perbandingan mingguan saja agar lebih akurat
        
        holidays = frappe.get_all("Holiday", 
            filters={"parent": holiday_list, "weekly_off": 1}, 
            fields=["holiday_date"], 
            limit=14) # Ambil 2 minggu sampel
            
        if not holidays:
            return 25
            
        # Hitung unik hari dalam seminggu (0=Mon, 6=Sun)
        unique_days = set()
        for h in holidays:
            unique_days.add(h.holiday_date.weekday())
            
        if len(unique_days) >= 2: # Libur 2 hari atau lebih dalam seminggu
            return 21
        else:
            return 25
            
    except Exception:
        return 25

@frappe.whitelist()
def calculate_pph21(doc, method=None):
	"""
	Menghitung PPh 21 bulanan untuk seorang karyawan berdasarkan data pada Salary Slip
	menggunakan metode Tarif Efektif Rerata (TER).
	"""
	try:
		employee = frappe.get_doc("Employee", doc.employee)
		status_ptkp = employee.status_pajak
		total_pendapatan_bruto_bulanan = doc.gross_pay

		if status_ptkp in ["TK/2", "TK/3", "K/1", "K/2"]:
			kategori_ter = "B"
		elif status_ptkp == "K/3":
			kategori_ter = "C"
		else:
			kategori_ter = "A"

		filters = {
			"kategori_ter": kategori_ter,
			"batas_penghasilan_bruto_bulanan_bawah": ["<=", total_pendapatan_bruto_bulanan],
			"batas_penghasilan_bruto_bulanan_atas": [">=", total_pendapatan_bruto_bulanan],
		}

		ter_item = frappe.get_list(
			"Tarif Efektif Rerata",
			filters=filters,
			fields=["tarif_ter"],
			limit=1,
		)

		if not ter_item:
			return 0

		ter_rate = ter_item[0].tarif_ter / 100
		pph21_bulanan = total_pendapatan_bruto_bulanan * ter_rate

		return round(pph21_bulanan)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Kalkulasi PPh 21 Gagal")
		return 0


@frappe.whitelist()
def calculate_overtime(doc, method=None):
	"""
	Menghitung total pendapatan lembur secara dinamis berdasarkan Overtime Planning.
	"""
	try:
		employee_id = doc.employee
		start_date = doc.start_date
		end_date = doc.end_date

		employee_doc = frappe.get_doc("Employee", employee_id)
		holiday_list_name = employee_doc.holiday_list
		if not holiday_list_name:
			return 0

		overtime_records = frappe.db.sql(
			f"""
            SELECT
                detail.start_time,
                detail.end_time,
                parent.overtime_date
            FROM
                `tabOvertime Planning Detail` AS detail
            JOIN
                `tabOvertime Planning` AS parent ON detail.parent = parent.name
            WHERE
                detail.employee = '{employee_id}'
                AND parent.docstatus = 1
                AND parent.overtime_date BETWEEN '{start_date}' AND '{end_date}'
        """,
			as_dict=True,
		)

		if not overtime_records:
			return 0

		gaji_sebulan = doc.base
		if not gaji_sebulan:
			return 0
		upah_per_jam = (1 / 173) * gaji_sebulan

		skema_cache = {}
		total_pendapatan_lembur = 0
		from frappe.utils import time_diff_in_hours

		for record in overtime_records:
			if not (record.start_time and record.end_time and record.overtime_date):
				continue

			jam_lembur_record = time_diff_in_hours(record.end_time, record.start_time)
			if not jam_lembur_record > 0:
				continue

			if is_holiday(holiday_list_name, record.overtime_date):
				skema_name = "Lembur Libur Resmi"
			else:
				skema_name = "Lembur Hari Kerja"

			if skema_name not in skema_cache:
				if frappe.db.exists("Overtime Calculation", skema_name):
					skema_cache[skema_name] = frappe.get_doc("Overtime Calculation", skema_name)
				else:
					continue

			skema_doc = skema_cache[skema_name]
			pendapatan_record = 0
			jam_tersisa = jam_lembur_record
			sorted_rates = sorted(skema_doc.overtime_rates, key=lambda x: x.jam_ke_mulai)

			for rate in sorted_rates:
				if jam_tersisa <= 0:
					break
				jam_mulai = rate.jam_ke_mulai
				jam_selesai = rate.jam_ke_selesai if rate.jam_ke_selesai > 0 else float("inf")
				pengali = rate.pengali_upah
				durasi_layer = (jam_selesai - jam_mulai) + 1 if jam_selesai != float("inf") else float("inf")
				jam_dihitung = min(jam_tersisa, durasi_layer)
				pendapatan_record += jam_dihitung * pengali * upah_per_jam
				jam_tersisa -= jam_dihitung

			total_pendapatan_lembur += pendapatan_record

		return round(total_pendapatan_lembur)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Kalkulasi Lembur Gagal")
		return 0
