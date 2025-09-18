import frappe


def run():
	print("--- Deleting all departments where is_group = 0 ---")
	try:
		depts_to_delete = frappe.get_all("Department", filters={"is_group": 0}, pluck="name")

		if not depts_to_delete:
			print(" -> No departments found with is_group = 0. Nothing to delete.")
			return

		print(f"Found {len(depts_to_delete)} departments to delete.")
		for dept_name in depts_to_delete:
			try:
				frappe.delete_doc("Department", dept_name, ignore_permissions=True, force=True)
				print(f"  - Deleted: {dept_name}")
			except Exception as e:
				print(f"  - ❌ ERROR deleting {dept_name}: {e}")

		frappe.db.commit()
		print("--- Deletion complete. ---")

	except Exception as e:
		print(f"An error occurred during deletion: {e}")
		frappe.db.rollback()
