import csv

import frappe
from frappe.utils import getdate
from frappe.utils.password import update_password


def is_valid_name(name):
	if not name or len(name) <= 1:
		return False
	if name.isdigit() or ("-" in name and name.replace("-", "").isdigit()):
		return False
	return True


def run_migration():
	company_name = "PT. SIUMANG TEMAN SUKSES"
	csv_file_path = "/Users/user/Projects/custom-siumang/DataKaryawan0925.csv"
	print(f"--- Starting Employee Migration for {company_name} ---")
	print(f"Reading from: {csv_file_path}")

	try:
		with open(csv_file_path, encoding="utf-8") as file:
			# Skip header row
			next(file)
			reader = csv.reader(file, delimiter=";")
			all_rows = list(reader)

			# create_dependencies(all_rows, company_name) # REMOVED: Dependencies are assumed to exist
			process_employee_data(all_rows, company_name)

		print("\n✨ Migration script finished successfully! ✨")

	except FileNotFoundError:
		print(f"ERROR: The file was not found at {csv_file_path}.")
	except Exception as e:
		print(f"A critical error occurred: {e}")
		frappe.db.rollback()


def process_employee_data(all_rows, company_name):
	print("--- Starting to process individual employees. ---")
	for i, row in enumerate(all_rows):
		if not (any(row) and len(row) > 2 and row[1].strip() and row[2].strip()):
			continue

		full_name = row[2].strip()
		print(f"\nProcessing row {i+2} for: '{full_name}'")

		try:
			nik, jabatan, department, section = row[1].strip(), row[3].strip(), row[4].strip(), row[5].strip()
			status_pegawai, date_of_joining = (
				row[6].strip(),
				getdate(row[7].strip()) if len(row) > 7 and row[7].strip() else None,
			)
			ktp, no_kk, place_of_birth = (
				(row[11].strip(), row[12].strip(), row[13].strip()) if len(row) > 13 else (None, None, None)
			)
			date_of_birth = getdate(row[14].strip()) if len(row) > 14 and row[14].strip() else None
			tax_status_code = (
				row[15].strip().upper().replace("/", "") if len(row) > 15 and row[15].strip() else None
			)
			gender, address = (row[16].strip(), row[18].strip()) if len(row) > 18 else (None, None)
			phone_number, emergency_contact = (
				(row[19].strip(), row[20].strip()) if len(row) > 20 else (None, None)
			)
			email, religion = (row[21].strip().lower(), row[22].strip()) if len(row) > 22 else (None, None)
			education_level, school, major = (
				(row[23].strip(), row[24].strip(), row[25].strip()) if len(row) > 25 else (None, None, None)
			)
			bank_name, bank_ac_no = (row[30].strip(), row[31].strip()) if len(row) > 31 else (None, None)
			bpjs_ketenagakerjaan, bpjs_kesehatan = (
				(row[32].strip(), row[33].strip()) if len(row) > 33 else (None, None)
			)
			blood_group = row[36].strip() if len(row) > 36 else None
			npwp = row[40].strip() if len(row) > 40 else None

			if not email or not nik or not full_name:
				continue

			user_id = create_user_if_not_exists(email, full_name, phone_number)

			if not frappe.db.exists("Employee", {"employee_number": nik}):
				print(f"Creating Employee: {full_name} ({nik})")

				employment_type = "Kontrak"
				if jabatan.lower() == "external":
					employment_type = "Outsourced"
				elif status_pegawai == "Tetap":
					employment_type = "Permanen"
				elif status_pegawai in ["Kontrak", "Harian", "Probation"]:
					employment_type = status_pegawai

				employee_doc = {
					"doctype": "Employee",
					"company": company_name,
					"employee_number": nik,
					"employee_name": full_name,
					"first_name": full_name.split()[0],
					"status": "Active",
					"user_id": user_id,
					"department": section or department,
					"designation": jabatan,
					"employment_type": employment_type,
					"date_of_joining": date_of_joining,
					"date_of_birth": date_of_birth,
					"gender": gender,
					"cell_number": phone_number,
					"personal_email": email,
					"permanent_address": address,
					"emergency_phone_number": emergency_contact,
					"bank_name": bank_name,
					"bank_ac_no": bank_ac_no,
					"blood_group": blood_group,
					"marital_status": "Married"
					if tax_status_code and tax_status_code.startswith("K")
					else "Single",
					"status_pajak": tax_status_code,
					"ktp": ktp,
					"npwp": npwp,
					"ikut_bpjs_kesehatan": 1 if bpjs_kesehatan else 0,
					"bpjs_kesehatan_id": bpjs_kesehatan,
					"ikut_bpjs_ketenagakerjaan": 1 if bpjs_ketenagakerjaan else 0,
					"bpjs_ketenagakerjaan_id": bpjs_ketenagakerjaan,
					"custom_agama": religion,
					"custom_tempat_lahir": place_of_birth,
					"custom_no_kk": no_kk,
					"education": [{"level": education_level, "school": school, "major": major}]
					if education_level and school
					else [],
				}

				frappe.get_doc(employee_doc).insert(ignore_permissions=True)
				print("  ✓ Successfully created Employee.")
			else:
				print(f" -> Employee with NIK {nik} already exists. Skipping.")

			frappe.db.commit()

		except Exception as e:
			print(f"\n❌ ERROR processing row {i+2} for '{full_name or 'Unknown'}': {e}")
			frappe.db.rollback()


def create_user_if_not_exists(email, full_name, phone_number):
	if not frappe.db.exists("User", email):
		print(f" -> Creating User: {email}")
		try:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": full_name.split()[0],
					"last_name": " ".join(full_name.split()[1:])
					if len(full_name.split()) > 1
					else full_name.split()[0],
					"send_welcome_email": 0,
					"roles": [{"role": "Employee"}],
				}
			)
			user.insert(ignore_permissions=True)

			if phone_number:
				update_password(user.name, phone_number)
				user.flags.force_password_reset = 1
				user.save(ignore_permissions=True)
				print("  ✓ Password set. Forced reset on next login.")
			else:
				print(f"  ⚠️ WARNING: No phone number for {email}, password not set.")
			return user.name
		except Exception as e:
			print(f"  ❌ ERROR creating User {email}: {e}")
			raise
	else:
		print(f" -> User {email} already exists. Skipping creation.")
		return email
