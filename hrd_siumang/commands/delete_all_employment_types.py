import frappe


def run():
	print("--- Deleting ALL Employment Type documents ---")
	try:
		all_emp_types = frappe.get_all("Employment Type", pluck="name")

		if not all_emp_types:
			print(" -> No Employment Type documents found. Table is already empty or nothing to delete.")
			return

		print(f"Found {len(all_emp_types)} Employment Type documents to delete.")
		for emp_type_name in all_emp_types:
			try:
				frappe.delete_doc("Employment Type", emp_type_name, ignore_permissions=True, force=True)
				print(f"  - Deleted: {emp_type_name}")
			except Exception as e:
				print(f"  - ❌ ERROR deleting {emp_type_name}: {e}")

		frappe.db.commit()
		print("--- All Employment Type documents deleted. ---")

	except Exception as e:
		print(f"An error occurred during deletion: {e}")
		frappe.db.rollback()
