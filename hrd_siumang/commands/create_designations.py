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
	print(f"--- Attempting to create Designations for {company_name} ---")

	try:
		with open(csv_file_path, encoding="utf-8") as file:
			next(file)  # Skip header
			reader = csv.reader(file, delimiter=";")
			all_rows = list(reader)

		designations = set()

		for row in all_rows:
			if any(row) and len(row) > 3 and row[1].strip() and row[2].strip():
				desg = row[3].strip()
				if is_valid_name(desg) and desg.lower() != "external":
					designations.add(desg)

		print(f" -> Found {len(designations)} unique designations to create.")

		for desg_name in designations:
			try:
				if not frappe.db.exists("Designation", desg_name):
					frappe.get_doc({"doctype": "Designation", "designation_name": desg_name}).insert(
						ignore_permissions=True
					)
					print(f"  - Created: {desg_name}")
				else:
					print(f"  - Skipping: {desg_name} already exists.")
			except Exception as e:
				print(f"  - ❌ ERROR creating {desg_name}: {e}")

		frappe.db.commit()
		print("--- Designations creation finished. ---")

	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
