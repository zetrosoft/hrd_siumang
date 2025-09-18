import csv
import random
import time  # Import time module
from datetime import datetime

import frappe


def create_employee_users():
	employees = frappe.get_all(
		"Employee",
		filters={"user_id": ["=", ""]},
		fields=["name", "employee_name", "personal_email", "department"],
	)

	if not employees:
		print("Tidak ada karyawan yang belum memiliki akun pengguna.")
		return

	print(f"Ditemukan {len(employees)} karyawan yang belum memiliki akun pengguna. Memulai pembuatan akun...")

	for employee in employees:
		employee_doc_name = employee.name
		employee_full_name = employee.employee_name
		employee_email = employee.personal_email
		employee_department = employee.department

		if not employee_email:
			print(
				f"Melewati karyawan {employee_full_name} (NIK: {employee_doc_name}) karena tidak memiliki alamat email pribadi."
			)
			continue

		# Generate a placeholder password. User MUST reset this.
		# In a real scenario, consider a more secure temporary password generation or a password reset flow.
		temp_password = frappe.generate_hash(employee_email + "temp_pass")[:8]  # Simple hash for placeholder

		try:
			# Create User document
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": employee_email,
					"first_name": employee_full_name.split(" ")[0] if employee_full_name else "",
					"last_name": " ".join(employee_full_name.split(" ")[1:])
					if len(employee_full_name.split(" ")) > 1
					else "",
					"full_name": employee_full_name,
					"new_password": temp_password,
					"send_welcome_email": 0,  # Do not send welcome email with temp password
					"enabled": 1,
					"user_type": "System User",
					"roles": [{"role": "Employee"}],
				}
			)
			user.insert(ignore_permissions=True)  # Use ignore_permissions if running as Administrator
			frappe.db.commit()
			print(
				f"  - Akun pengguna untuk {employee_full_name} ({employee_email}) berhasil dibuat. Password sementara: {temp_password}"
			)

			# Link User to Employee
			frappe.db.set_value("Employee", employee_doc_name, "user_id", user.name)
			frappe.db.commit()
			print(f"  - Akun pengguna berhasil dihubungkan dengan karyawan {employee_full_name}.")

			# Set User Permissions for Employee DocType (self-only)
			if not frappe.db.exists(
				"User Permission", {"user": user.name, "allow": "Employee", "for_value": employee_doc_name}
			):
				user_perm_employee = frappe.get_doc(
					{
						"doctype": "User Permission",
						"user": user.name,
						"allow": "Employee",
						"for_value": employee_doc_name,
						"is_default": 1,
					}
				)
				user_perm_employee.insert(ignore_permissions=True)
				frappe.db.commit()
				print("  - Izin pengguna untuk DocType Employee (hanya diri sendiri) berhasil diatur.")

			# Set User Permissions for Department (department-specific)
			if employee_department:
				try:
					if not frappe.db.exists(
						"User Permission",
						{"user": user.name, "allow": "Department", "for_value": employee_department},
					):
						user_perm_dept = frappe.get_doc(
							{
								"doctype": "User Permission",
								"user": user.name,
								"allow": "Department",
								"for_value": employee_department,
								"is_default": 1,
							}
						)
						user_perm_dept.insert(ignore_permissions=True)
						frappe.db.commit()
						print(
							f"  - Izin pengguna untuk DocType Department ({employee_department}) berhasil diatur."
						)
				except Exception as dept_e:
					print(
						f"  - Gagal mengatur izin departemen untuk {employee_full_name} ({employee_department}): {dept_e}"
					)

		except Exception as e:
			frappe.db.rollback()
			print(f"Gagal membuat/mengatur akun pengguna untuk {employee_full_name} ({employee_email}): {e}")

		time.sleep(1.0)  # Increased delay to 1 second to avoid throttling

	print("\nProses pembuatan akun pengguna selesai.")


if __name__ == "__main__":
	create_employee_users()
