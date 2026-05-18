import frappe
from frappe.utils import getdate


def debug_employee_for_payroll():
	"""
	Inspects a specific employee's data relevant for payroll processing
	to debug "No employees found" errors in Process Payroll.
	"""
	employee_id = "HR-EMP-00003"
	start_date_str = "2025-09-01"
	end_date_str = "2025-09-30"

	try:
		frappe.set_user("Administrator")
		print(f"\n--- Memeriksa Data Payroll untuk Karyawan: {employee_id} ---")
		print(f"--- Periode Penggajian: {start_date_str} s/d {end_date_str} ---")

		# Konversi tanggal
		start_date = getdate(start_date_str)
		end_date = getdate(end_date_str)

		# 1. Periksa Data Karyawan
		if not frappe.db.exists("Employee", employee_id):
			print(f"\n[HASIL]: ❌ KESALAHAN: Karyawan {employee_id} tidak ditemukan.")
			return

		emp = frappe.get_doc("Employee", employee_id)
		print("\n[1. Data Karyawan]")
		print(f"  - Nama: {emp.employee_name}")
		print(f"  - Status: {emp.status}")
		print(f"  - Tanggal Bergabung: {emp.date_of_joining}")
		print(f"  - Tanggal Berhenti: {emp.relieving_date}")

		# Analisis Status & Tanggal Karyawan
		is_valid = True
		if emp.status != "Active":
			print("  - ⚠️ MASALAH: Status karyawan bukan 'Active'.")
			is_valid = False
		if emp.date_of_joining and getdate(emp.date_of_joining) > end_date:
			print(
				f"  - ⚠️ MASALAH: Karyawan baru bergabung ({emp.date_of_joining}) setelah periode gaji berakhir ({end_date_str})."
			)
			is_valid = False
		if emp.relieving_date and getdate(emp.relieving_date) < start_date:
			print(
				f"  - ⚠️ MASALAH: Karyawan sudah berhenti ({emp.relieving_date}) sebelum periode gaji dimulai ({start_date_str})."
			)
			is_valid = False

		# 2. Periksa Salary Structure Assignment (SSA)
		ssa_list = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": employee_id, "docstatus": 1, "from_date": ("<=", start_date)},
			fields=["name", "from_date", "salary_structure"],  # 'to_date' dihapus
			order_by="from_date desc",
			limit=1,
		)

		print("\n[2. Salary Structure Assignment (SSA)]")
		if not ssa_list:
			print(
				f"  - ⚠️ MASALAH: Tidak ditemukan SSA yang AKTIF dan BERLAKU pada atau sebelum {start_date_str}."
			)
			is_valid = False
		else:
			ssa = ssa_list[0]
			print(f"  - Ditemukan Assignment: {ssa.name}")
			print(f"  - Berlaku Sejak: {ssa.from_date}")

		# 3. Kesimpulan Akhir
		print("\n[3. KESIMPULAN]")
		if is_valid:
			print(
				f"✅ Berdasarkan data, karyawan '{emp.employee_name}' SEHARUSNYA ditemukan oleh Process Payroll."
			)
			print("   Jika masalah masih terjadi, periksa hal berikut:")
			print(
				"   - Apakah ada slip gaji lain yang tumpang tindih untuk karyawan ini di periode yang sama?"
			)
			print("   - Coba bersihkan cache (`bench clear-cache` atau dari UI).")
			print(
				"   - Pastikan tidak ada filter lain (Branch, Designation) yang Anda terapkan di Process Payroll."
			)
		else:
			print(
				f"❌ Karyawan '{emp.employee_name}' TIDAK AKAN ditemukan oleh Process Payroll karena masalah yang ditandai '⚠️' di atas."
			)

	except Exception as e:
		print(f"❌ GAGAL saat menjalankan inspeksi: {e}")


def run():
	"""Wrapper function to be called by bench execute."""
	debug_employee_for_payroll()
