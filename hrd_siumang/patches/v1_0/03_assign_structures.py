# Patch 3: Membuat Salary Structure Assignments
import frappe
from frappe.utils import nowdate


def execute():
	"""Membuat Salary Structure Assignment untuk setiap karyawan aktif."""
	frappe.set_user("Administrator")
	print("Memulai Patch: Membuat Salary Structure Assignments...")

	employees = frappe.get_list(
		"Employee",
		filters={"status": "Active", "company": "PT. SIUMANG TEMAN SUKSES"},
		fields=["name", "employee_name", "ctc", "employment_type", "date_of_joining"],
	)

	if not employees:
		print("Tidak ada karyawan aktif ditemukan. Patch dilewati.")
		return

	for emp in employees:
		if not emp.employment_type:
			print(f"⚠️ PERINGATAN: Karyawan '{emp.employee_name}' tidak memiliki Employment Type. Melewati.")
			continue

		structure_name = f"Struktur Gaji - {emp.employment_type}"
		if not frappe.db.exists("Salary Structure", structure_name):
			print(
				f"❌ GAGAL: Salary Structure '{structure_name}' untuk karyawan '{emp.employee_name}' tidak ditemukan. Jalankan patch kedua terlebih dahulu."
			)
			continue

		if not frappe.db.exists("Salary Structure Assignment", {"employee": emp.name, "docstatus": 1}):
			try:
				ssa = frappe.new_doc("Salary Structure Assignment")
				ssa.employee = emp.name
				ssa.salary_structure = structure_name
				ssa.from_date = emp.date_of_joining
				ssa.base = emp.ctc
				ssa.save(ignore_permissions=True)
				ssa.submit()
				print(f"✅ BERHASIL: Assignment untuk '{emp.employee_name}' ke '{structure_name}' dibuat.")
			except Exception as e:
				print(f"❌ GAGAL saat membuat assignment untuk '{emp.employee_name}': {e}")
				frappe.db.rollback()
		else:
			print(f"[INFO] Assignment untuk '{emp.employee_name}' sudah ada.")

	frappe.db.commit()
	print("Patch 'assign_structures' selesai.")
