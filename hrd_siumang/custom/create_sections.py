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
	print("--- Attempting to create Sections (Sub-Departments) ---")

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
					sections_to_link.add((dept, sect))

		print(f" -> Found {len(sections_to_link)} unique section relationships.")

		print(" -> Pass 1: Ensuring all department entities exist first...")
		for name in all_dept_names:
			# Correct existence check
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
					print(f"  - Skipping: Cannot link '{child_name}' to itself.")
					continue

				# Fetch child doc by filters to be safe
				child_doc = frappe.get_doc(
					"Department", {"department_name": child_name, "company": company_name}
				)
				if not child_doc.parent_department:
					child_doc.parent_department = parent_name
					child_doc.save(ignore_permissions=True)
					print(f"  - Linked '{child_name}' to parent '{parent_name}'.")
				else:
					print(f"  - Skipping: '{child_name}' already has a parent.")
			except Exception as e:
				print(f"  - ❌ ERROR: Could not link {child_name} to {parent_name}. Reason: {e}")
		frappe.db.commit()
		print("     Done.")

		print("--- Script finished. ---")

	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
