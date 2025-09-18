import frappe


def run():
	print("--- Deleting ALL Department documents ---")
	try:
		all_depts = frappe.get_all("Department", pluck="name")

		if not all_depts:
			print(" -> No Department documents found. Table is already empty or nothing to delete.")
			return

		print(f"Found {len(all_depts)} Department documents to delete.")
		for dept_name in all_depts:
			try:
				frappe.delete_doc("Department", dept_name, ignore_permissions=True, force=True)
				print(f"  - Deleted: {dept_name}")
			except Exception as e:
				print(f"  - ❌ ERROR deleting {dept_name}: {e}")

		frappe.db.commit()
		print("--- All Department documents deleted. ---")

	except Exception as e:
		print(f"An error occurred during deletion: {e}")
		frappe.db.rollback()
