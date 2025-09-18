import frappe


def run():
	print("--- Deleting ALL Designation documents ---")
	try:
		all_desgs = frappe.get_all("Designation", pluck="name")

		if not all_desgs:
			print(" -> No Designation documents found. Table is already empty or nothing to delete.")
			return

		print(f"Found {len(all_desgs)} Designation documents to delete.")
		for desg_name in all_desgs:
			try:
				frappe.delete_doc("Designation", desg_name, ignore_permissions=True, force=True)
				print(f"  - Deleted: {desg_name}")
			except Exception as e:
				print(f"  - ❌ ERROR deleting {desg_name}: {e}")

		frappe.db.commit()
		print("--- All Designation documents deleted. ---")

	except Exception as e:
		print(f"An error occurred during deletion: {e}")
		frappe.db.rollback()
