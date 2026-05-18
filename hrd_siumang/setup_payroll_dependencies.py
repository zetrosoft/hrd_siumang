import frappe
from frappe import _


def check_overtime_calculation_documents():
	"""
	Checks if 'Lembur Libur Resmi' and 'Lembur Hari Kerja' Overtime Calculation
	documents exist and prints their status.
	"""
	frappe.set_user("Administrator")  # Ensure we have necessary permissions

	required_schemes = ["Lembur Libur Resmi", "Lembur Hari Kerja"]
	print("\n--- Status Dokumen Overtime Calculation ---")
	for scheme_name in required_schemes:
		if frappe.db.exists("Overtime Calculation", scheme_name):
			print(f"✅ Dokumen '{scheme_name}' sudah ada.")
		else:
			print(f"❌ Dokumen '{scheme_name}' BELUM ada. Mohon buat dokumen ini secara manual.")
	print("-------------------------------------------\n")


def assign_holiday_list_to_employees():
	"""
	Assigns a default Holiday List to employees who don't have one set.
	"""
	frappe.set_user("Administrator")  # Ensure we have necessary permissions

	print("\n--- Menautkan Holiday List ke Karyawan ---")

	# 1. Dapatkan Holiday List default
	default_holiday_list = frappe.db.get_value(
		"Holiday List", filters={}, fieldname="name", order_by="creation asc"
	)

	if not default_holiday_list:
		print(
			"❌ Tidak ada Dokumen Holiday List yang ditemukan di sistem. Mohon buat Holiday List terlebih dahulu."
		)
		return

	print(f"Menggunakan Holiday List default: '{default_holiday_list}'")

	# 2. Dapatkan semua karyawan yang belum punya Holiday List
	employees_to_update = frappe.get_all(
		"Employee", filters={"holiday_list": ["is", "not set"]}, fields=["name", "employee_name"]
	)

	if not employees_to_update:
		print("✅ Semua karyawan sudah memiliki Holiday List atau tidak ada karyawan yang perlu diperbarui.")
		return

	print(f"Ditemukan {len(employees_to_update)} karyawan yang Holiday List-nya kosong.")

	# 3. Perbarui karyawan
	updated_count = 0
	for employee in employees_to_update:
		try:
			frappe.db.set_value(
				"Employee", employee.name, "holiday_list", default_holiday_list, update_modified=False
			)
			updated_count += 1
			print(
				f"   - ✅ Berhasil menautkan '{default_holiday_list}' ke Karyawan: {employee.employee_name} ({employee.name})"
			)
		except Exception as e:
			print(f"   - ❌ Gagal menautkan ke Karyawan {employee.employee_name} ({employee.name}): {e}")

	frappe.db.commit()
	print("-----------------------------------------------------")
	print(f"✅ Berhasil menautkan '{default_holiday_list}' ke {updated_count} karyawan.")
	print("-----------------------------------------------------\\n")


if __name__ == "__main__":
	# This block is for direct execution, but bench execute will call functions directly.
	# For a more robust bench execute, we would define separate entry points.
	pass
