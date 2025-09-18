import frappe


def run():
	print("--- Attempting to create Employment Types ---")
	emp_types = ["Permanen", "Kontrak", "Harian", "Probation", "Outsourced"]

	try:
		for emp_type_name in emp_types:
			if not frappe.db.exists("Employment Type", emp_type_name):
				frappe.get_doc({"doctype": "Employment Type", "name": emp_type_name}).insert(
					ignore_permissions=True
				)
				print(f"  - Created: {emp_type_name}")
			else:
				print(f"  - Skipping: {emp_type_name} already exists.")

		frappe.db.commit()
		print("--- Employment Types creation finished. ---")

	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
