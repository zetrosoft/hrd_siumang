import csv

import frappe
from frappe.utils.password import update_password


def run_migration():
	"""
	Reads employee data from a CSV file and migrates it to Frappe ERPNext.

	This script performs the following actions:
	1.  Reads a predefined CSV file containing employee data.
	2.  Ensures dependent records (Department, Designation) exist, creating them if necessary.
	3.  For each employee in the CSV:
	    a. Creates a new Frappe User with their email as the user ID.
	    b. Sets their phone number as a temporary password and forces a password reset on first login.
	    c. Creates a new Employee document with the detailed information from the CSV.
	    d. Links the User and other records to the new Employee document.
	"""
	company_name = "PT. SIUMANG TEMAN SUKSES"
	csv_file_path = "/Users/user/Projects/custom-siumang/DataKaryawan0925.csv"

	try:
		with open(csv_file_path) as file:
			reader = csv.reader(file)
			# Skip the first 4 header rows
			for _ in range(4):
				next(reader)

			all_rows = list(reader)

			# --- Step 1: Pre-process and create dependencies ---
			departments = set()
			designations = set()

			for row in all_rows:
				if not any(row):
					continue  # Skip empty rows
				try:
					department = row[5].strip()
					designation = row[4].strip()
					if department:
						departments.add(department)
					if designation:
						designations.add(designation)
				except IndexError:
					print(f"Skipping malformed row (dependency scan): {row}")
					continue
			frappe.throw(departments)
			print("--- Creating Departments ---")
			for dept_name in departments:
				if not frappe.db.exists(
					"Department", {"department_name": dept_name, "company": company_name}
				):
					try:
						doc = frappe.get_doc(
							{"doctype": "Department", "department_name": dept_name, "company": company_name}
						)
						doc.insert(ignore_permissions=True)
						print(f"Created Department: {dept_name}")
					except Exception as e:
						print(f"Error creating Department {dept_name}: {e}")
				else:
					print(f"Department {dept_name} already exists.")

			print("--- Creating Designations ---")
			for desg_name in designations:
				if not frappe.db.exists("Designation", {"designation_name": desg_name}):
					try:
						doc = frappe.get_doc({"doctype": "Designation", "designation_name": desg_name})
						doc.insert(ignore_permissions=True)
						print(f"Created Designation: {desg_name}")
					except Exception as e:
						print(f"Error creating Designation {desg_name}: {e}")
				else:
					print(f"Designation {desg_name} already exists.")

			frappe.db.commit()
			print("\n--- Dependencies created. Starting User and Employee migration ---")

			# --- Step 2: Create Users and Employees ---
			for i, row in enumerate(all_rows):
				if not any(row):
					continue

				try:
					# --- Column Mapping (adjust indices if CSV structure changes) ---
					nik = row[2].strip()
					full_name = row[3].strip()
					designation = row[4].strip()
					department = row[5].strip()
					status_pegawai = row[7].strip()
					date_of_joining = row[8].strip() if row[8].strip() else None
					date_of_birth = row[19].strip() if row[19].strip() else None
					gender = row[21].strip()
					address = row[23].strip()
					phone_number = row[24].strip()
					emergency_contact = row[25].strip()
					email = row[26].strip().lower()

					if not email or not nik or not full_name:
						print(f"Skipping row {i+5} due to missing essential data (Email, NIK, or Name).")
						continue

					# --- Create User ---
					user_id = email
					if not frappe.db.exists("User", user_id):
						print(f"Creating User: {user_id}")
						try:
							name_parts = full_name.split()
							first_name = name_parts[0]
							last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else first_name

							user = frappe.get_doc(
								{
									"doctype": "User",
									"email": user_id,
									"first_name": first_name,
									"last_name": last_name,
									"send_welcome_email": 0,
									"roles": [{"role": "Employee"}],
								}
							)
							user.insert(ignore_permissions=True)

							# Set temporary password and force reset
							if phone_number:
								update_password(user.name, phone_number)
								user.flags.force_password_reset = 1
								user.save(ignore_permissions=True)
								print("  - Password set to phone number.")
								print("  - Forced password reset on next login.")
							else:
								print(f"  - WARNING: No phone number for {user_id}, password not set.")

						except Exception as e:
							print(f"  - ERROR creating User {user_id}: {e}")
							frappe.db.rollback()
							continue
					else:
						print(f"User {user_id} already exists. Skipping user creation.")

					# --- Create Employee ---
					if not frappe.db.exists("Employee", {"employee_number": nik}):
						print(f"Creating Employee: {full_name} ({nik})")
						try:
							employee = frappe.get_doc(
								{
									"doctype": "Employee",
									"employee_number": nik,
									"employee_name": full_name,
									"first_name": full_name.split()[0],
									"company": company_name,
									"department": department,
									"designation": designation,
									"status": "Active"
									if status_pegawai in ["Tetap", "Probation", "Kontrak"]
									else "Left",
									"date_of_joining": frappe.utils.getdate(date_of_joining),
									"date_of_birth": frappe.utils.getdate(date_of_birth),
									"gender": gender,
									"cell_number": phone_number,
									"personal_email": email,
									"user_id": user_id,
									"permanent_address": address,
									"emergency_phone_number": emergency_contact,
								}
							)
							employee.insert(ignore_permissions=True)
							print("  - Successfully created Employee.")
						except Exception as e:
							print(f"  - ERROR creating Employee {full_name}: {e}")
							frappe.db.rollback()
							continue
					else:
						print(f"Employee with NIK {nik} already exists. Skipping employee creation.")

					frappe.db.commit()
					print("-" * 20)

				except IndexError:
					print(f"Skipping malformed row (main processing): {row}")
					frappe.db.rollback()
					continue
				except Exception as e:
					print(f"An unexpected error occurred on row {i+5}: {e}")
					frappe.db.rollback()
					continue

		print("\nMigration script finished.")

	except FileNotFoundError:
		print(f"ERROR: The file was not found at {csv_file_path}")
	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()
