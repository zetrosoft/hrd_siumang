import frappe


def run():
	company_name = "PT. SIUMANG TEMAN SUKSES"
	print(f"--- Inserting hardcoded Department tree for {company_name} ---")

	# Hardcoded tree structure based on our last discussion
	# Order matters for parent-child linking
	department_data = [
		{"name": "All Departments", "parent": None, "is_group": 1},  # Root node
		{"name": "Operasional", "parent": "All Departments", "is_group": 1},
		{"name": "HR & GA", "parent": "All Departments", "is_group": 1},
		{"name": "FAT", "parent": "All Departments", "is_group": 1},
		{
			"name": "Purchasing",
			"parent": "All Departments",
			"is_group": 0,
		},  # Note: is_group=0 as per user's last table
		{"name": "Management", "parent": "All Departments", "is_group": 1},
		{"name": "Content", "parent": "All Departments", "is_group": 1},
		{"name": "Marketplace", "parent": "Sales", "is_group": 1},  # Parent is Sales, not ALL
		{"name": "Sales", "parent": "All Departments", "is_group": 1},
		{"name": "QC, QA & RND", "parent": "All Departments", "is_group": 1},
		{"name": "Warehouse & Logistics", "parent": "All Departments", "is_group": 1},
		{"name": "Produksi", "parent": "All Departments", "is_group": 1},
		{"name": "Engineering", "parent": "All Departments", "is_group": 1},
		# Sections (children)
		{"name": "Production", "parent": "Operasional", "is_group": 0},
		{"name": "HRGA", "parent": "HR & GA", "is_group": 0},
		{"name": "GA", "parent": "HR & GA", "is_group": 0},
		{"name": "Security", "parent": "HR & GA", "is_group": 0},
		{"name": "Finance", "parent": "FAT", "is_group": 0},
		{"name": "Personal Assistant", "parent": "Management", "is_group": 0},
		{"name": "Sosial Media Specialist", "parent": "Content", "is_group": 0},
		{"name": "Videographer", "parent": "Content", "is_group": 0},
		{"name": "Script writer", "parent": "Content", "is_group": 0},
		{"name": "Talent", "parent": "Content", "is_group": 0},
		{"name": "Editor", "parent": "Content", "is_group": 0},
		{"name": "Editor Video", "parent": "Content", "is_group": 0},
		{"name": "Wardrobe", "parent": "Content", "is_group": 0},
		{"name": "Live Streaming", "parent": "Marketplace", "is_group": 0},
		{"name": "Administration", "parent": "Sales", "is_group": 0},
		{"name": "Quality Control", "parent": "QC, QA & RND", "is_group": 0},
		{"name": "Market Place", "parent": "Warehouse & Logistics", "is_group": 0},
		{"name": "Driver", "parent": "Warehouse & Logistics", "is_group": 0},
		{"name": "Administration", "parent": "Warehouse & Logistics", "is_group": 0},
		{"name": "Administration", "parent": "Produksi", "is_group": 0},
		{"name": "Bungkus", "parent": "Produksi", "is_group": 0},
		{"name": "Finishing", "parent": "Produksi", "is_group": 0},
		{"name": "Giling", "parent": "Produksi", "is_group": 0},
		{"name": "Masak", "parent": "Produksi", "is_group": 0},
		{"name": "Cleaning Service", "parent": "Produksi", "is_group": 0},
		{"name": "Teknisi", "parent": "Engineering", "is_group": 0},
	]

	try:
		# Ensure All Departments root exists and is a group
		root_doc_name = "All Departments"
		if not frappe.db.exists("Department", root_doc_name):
			frappe.get_doc(
				{
					"doctype": "Department",
					"department_name": root_doc_name,
					"company": company_name,
					"is_group": 1,
				}
			).insert(ignore_permissions=True)
			frappe.db.commit()
			print(f"  - Created root department: {root_doc_name}")
		else:
			# Ensure it's a group if it exists
			root_doc = frappe.get_doc("Department", root_doc_name)
			if not root_doc.is_group:
				root_doc.is_group = 1
				root_doc.save(ignore_permissions=True)
				frappe.db.commit()
			print(f"  - Root department {root_doc_name} already exists.")

		# First pass: Create all departments without parent links (or with root link)
		for data in department_data:
			dept_name = data["name"]
			if not frappe.db.exists("Department", {"department_name": dept_name, "company": company_name}):
				doc = frappe.get_doc(
					{
						"doctype": "Department",
						"department_name": dept_name,
						"company": company_name,
						"is_group": data["is_group"],
						"parent_department": root_doc_name
						if data["parent"] == "All Departments"
						else None,  # Link to root if top-level
					}
				)
				doc.insert(ignore_permissions=True)
				print(f"  - Created: {dept_name} (is_group={data['is_group']})")
			else:
				print(f"  - Skipping: {dept_name} already exists.")
		frappe.db.commit()
		print(" -> Pass 1: All department entities created/checked.")

		# Second pass: Set parent links for non-root departments and update is_group for parents
		for data in department_data:
			dept_name = data["name"]
			parent_name = data["parent"]

			if parent_name and parent_name != root_doc_name:
				try:
					child_doc = frappe.get_doc(
						"Department", {"department_name": dept_name, "company": company_name}
					)
					parent_doc_id = frappe.db.get_value(
						"Department", {"department_name": parent_name, "company": company_name}, "name"
					)

					if not parent_doc_id:
						print(
							f"  - ⚠️ WARNING: Parent '{parent_name}' for '{dept_name}' not found. Skipping link."
						)
						continue

					if child_doc.parent_department != parent_doc_id:
						child_doc.parent_department = parent_doc_id
						child_doc.save(ignore_permissions=True)
						print(f"  - Linked '{dept_name}' to parent '{parent_name}'.")
					else:
						print(f"  - '{dept_name}' already correctly linked to '{parent_name}'.")

					# Ensure parent is marked as group
					parent_doc = frappe.get_doc("Department", parent_doc_id)
					if not parent_doc.is_group:
						parent_doc.is_group = 1
						parent_doc.save(ignore_permissions=True)

				except Exception as e:
					print(f"  - ❌ ERROR linking/updating {dept_name} to {parent_name}: {e}")
		frappe.db.commit()
		print(" -> Pass 2: Parent links set and group status updated.")

		print("--- Department tree insertion finished. ---")

	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
