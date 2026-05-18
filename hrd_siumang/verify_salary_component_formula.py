import frappe


def verify_formula():
	"""
	Fetches the 'Overtime' Salary Component and prints its formula.
	"""
	frappe.set_user("Administrator")  # Ensure permissions

	component_name = "Overtime"

	print(f"\n--- Memverifikasi Formula untuk Salary Component '{component_name}' ---")

	try:
		# Fetch the Salary Component document
		component = frappe.get_doc("Salary Component", component_name)

		# Print the formula field
		formula_value = component.get("formula")

		print(f"Formula saat ini untuk '{component_name}': {formula_value}")

		expected_formula = "doc.get_overtime_amount()"
		if formula_value == expected_formula:
			print(f"✅ Formula cocok dengan yang diharapkan: '{expected_formula}'.")
		else:
			print(f"❌ Formula TIDAK cocok. Diharapkan: '{expected_formula}', Ditemukan: '{formula_value}'.")
			print("Mohon perbaiki secara manual di UI Frappe.")

	except frappe.DoesNotExistError:
		print(f"❌ Salary Component '{component_name}' tidak ditemukan.")
	except Exception as e:
		print(f"❌ Gagal memverifikasi formula: {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Verifikasi Formula Salary Component")

	print("-------------------------------------------------------------------\n")
