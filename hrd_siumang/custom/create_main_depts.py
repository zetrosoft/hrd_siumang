import frappe


def run():
	company_name = "PT. SIUMANG TEMAN SUKSES"
	department_list = [
		"Operasional",
		"HR & GA",
		"FAT",
		"Purchasing",
		"Management",
		"Content",
		"Marketplace",
		"Sales",
		"QC, QA & RND",
		"Warehouse & Logistics",
		"Produksi",
		"Engineering",
	]

	print("--- Attempting to create 12 main departments ---")

	# In Frappe, the top-level parent for a tree structure is the name of the DocType itself.
	# The user requested 'ALL', but the conventional root is the Doctype name.
	# However, some setups might use a root node named 'All Departments'.
	# Let's try creating a root node first if it doesn't exist.
	root_department = "All Departments"
	if not frappe.db.exists("Department", root_department):
		try:
			frappe.get_doc(
				{
					"doctype": "Department",
					"department_name": root_department,
					"is_group": 1,
					"company": company_name,
				}
			).insert(ignore_permissions=True)
			frappe.db.commit()
			print(f"Created root department: '{root_department}'")
		except Exception as e:
			print(f"Could not create root department. This might be okay. Error: {e}")

	for dept_name in department_list:
		try:
			if not frappe.db.exists("Department", {"department_name": dept_name, "company": company_name}):
				print(f"Creating: {dept_name}")
				frappe.get_doc(
					{
						"doctype": "Department",
						"department_name": dept_name,
						"company": company_name,
						"is_group": 1,
						"parent_department": root_department,
					}
				).insert(ignore_permissions=True)
				frappe.db.commit()
				print(" -> Success.")
			else:
				print(f"Skipping: {dept_name} already exists.")
		except Exception as e:
			print(f"\n❌ ERROR creating '{dept_name}': {e}")
			frappe.db.rollback()
			break  # Stop on first error

	print("--- Script finished. ---")
