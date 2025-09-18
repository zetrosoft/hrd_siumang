import csv

import frappe


def is_valid_name(name):
	if not name or len(name) <= 1:
		return False
	if name.isdigit() or ("-" in name and name.replace("-", "").isdigit()):
		return False
	return True


def run():
	company_name = "PT. SIUMANG TEMAN SUKSES"
	csv_file_path = "/Users/user/Projects/custom-siumang/DataKaryawan0925.csv"
	print(f"--- Rebuilding entire department tree for {company_name} ---")

	try:
		with open(csv_file_path, encoding="utf-8") as file:
			next(file)  # Skip header
			reader = csv.reader(file, delimiter=";")
			all_rows = list(reader)

		all_dept_names, sections_to_link = set(), set()

		for row in all_rows:
			if any(row) and len(row) > 5 and row[1].strip() and row[2].strip():
				dept, sect = row[4].strip(), row[5].strip()
				if is_valid_name(dept):
					all_dept_names.add(dept)
				if is_valid_name(sect):
					all_dept_names.add(sect)
					if is_valid_name(dept):
						sections_to_link.add((dept, sect))

		print(f" -> Found {len(all_dept_names)} total department entities to create.")

		print(" -> Pass 1: Creating all department entities...")
		for name in all_dept_names:
			if not frappe.db.exists("Department", {"department_name": name, "company": company_name}):
				frappe.get_doc(
					{"doctype": "Department", "department_name": name, "company": company_name}
				).insert(ignore_permissions=True)
		frappe.db.commit()
		print("     Done.")

		print(" -> Pass 2: Setting parent-child links for sections...")
		for parent_name, child_name in sections_to_link:
			try:
				if parent_name == child_name:
					continue

				parent_doc_id = frappe.db.get_value(
					"Department", {"department_name": parent_name, "company": company_name}, "name"
				)
				if not parent_doc_id:
					print(
						f"  - ⚠️ WARNING: Could not find parent '{parent_name}' in database. Skipping link for '{child_name}'."
					)
					continue

				child_doc = frappe.get_doc(
					"Department", {"department_name": child_name, "company": company_name}
				)
				if not child_doc.parent_department:
					child_doc.parent_department = parent_doc_id

					parent_doc = frappe.get_doc("Department", parent_doc_id)
					if not parent_doc.is_group:
						parent_doc.is_group = 1
						parent_doc.save(ignore_permissions=True)

					child_doc.save(ignore_permissions=True)
					print(f"  - Linked '{child_name}' to parent '{parent_name}'.")

			except Exception as e:
				print(f"  - ❌ ERROR: Could not link {child_name} to {parent_name}. Reason: {e}")
		frappe.db.commit()
		print("     Done.")

		print("--- Department tree rebuild finished. ---")

	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
