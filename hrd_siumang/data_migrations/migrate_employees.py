import csv
import random
from datetime import datetime

import frappe


def parse_date(date_str):
	if not date_str or date_str.strip() == "-":
		return None
	date_str = date_str.strip()
	try:
		# Try DD/MM/YYYY format
		return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
	except ValueError:
		try:
			# Try DD-Mon-YY format
			return datetime.strptime(date_str, "%d-%b-%y").strftime("%Y-%m-%d")
		except ValueError:
			try:
				# Try DD/MM/YY format
				return datetime.strptime(date_str, "%d/%m/%y").strftime("%Y-%m-%d")
			except ValueError:
				return None  # Or raise an error if strict parsing is needed


def migrate_employee_data():
	csv_file_path = "/Users/user/Projects/custom-siumang/DataKaryawan0925.csv"

	# List of NIKs to process. Empty list means process all.
	# If you want to process only failed ones, populate this list with their NIKs.
	# For a full re-run, you might want to clear this list or comment out the filter
	niks_to_process = []

	# Mapping CSV headers to Frappe Employee DocType fields

	default_company = "PT. SIUMANG TEMAN SUKSES"
	default_naming_series = "HR-EMP-"

	print(f"Memulai migrasi data karyawan dari {csv_file_path}")

	with open(csv_file_path, encoding="utf-8") as csvfile:
		# Use csv.reader with SEMICOLON as delimiter
		reader = csv.reader(csvfile, delimiter=";")
		headers = [h.strip() for h in next(reader)]  # Read header row

		# Create a dictionary for header to index mapping
		header_to_idx = {header: idx for idx, header in enumerate(headers)}

		for i, row in enumerate(reader):
			if not row:
				continue

			if len(row) < len(headers) / 2:
				print(f"Baris {i+1} terlalu pendek, dilewati.")
				continue

			current_nik = row[header_to_idx.get("NIK", "")].strip()
			if niks_to_process and current_nik not in niks_to_process:
				continue

			print(f"\nMemproses baris {i+1}: {row[header_to_idx.get('Nama', 'N/A')]}")

			employee_data = {}

			employee_data["doctype"] = "Employee"
			employee_data["naming_series"] = default_naming_series
			employee_data["company"] = default_company
			employee_data["status"] = "Active"

			employee_data["employee_number"] = (
				row[header_to_idx.get("NIK", None)].strip() if header_to_idx.get("NIK") is not None else None
			)

			full_name = (
				row[header_to_idx.get("Nama", None)].strip() if header_to_idx.get("Nama") is not None else ""
			)
			name_parts = full_name.split(" ")
			employee_data["first_name"] = name_parts[0] if name_parts else ""
			employee_data["middle_name"] = name_parts[1] if len(name_parts) > 2 else ""
			employee_data["last_name"] = name_parts[-1] if len(name_parts) > 1 else ""
			employee_data["employee_name"] = full_name

			jabatan_val = (
				row[header_to_idx.get("Jabatan", None)].strip()
				if header_to_idx.get("Jabatan") is not None
				else None
			)
			employee_data["designation"] = jabatan_val
			employee_data["jabatan"] = jabatan_val

			employee_data["department"] = (
				row[header_to_idx.get("Departemen", None)].strip()
				if header_to_idx.get("Departemen") is not None
				else None
			)

			employment_type_val = (
				row[header_to_idx.get("Status Pegawai", None)].strip()
				if header_to_idx.get("Status Pegawai") is not None
				else None
			)
			employee_data["employment_type"] = employment_type_val

			employee_data["date_of_joining"] = (
				parse_date(row[header_to_idx.get("Date Join", None)].strip())
				if header_to_idx.get("Date Join") is not None
				else None
			)
			employee_data["date_of_birth"] = (
				parse_date(row[header_to_idx.get("Date Of Birth", None)].strip())
				if header_to_idx.get("Date Of Birth") is not None
				else None
			)

			employee_data["ktp"] = (
				row[header_to_idx.get("NIK KTP", None)].strip()
				if header_to_idx.get("NIK KTP") is not None
				else None
			)
			employee_data["custom_no_kk"] = (
				row[header_to_idx.get("No KK", None)].strip()
				if header_to_idx.get("No KK") is not None
				else None
			)
			employee_data["custom_tempat_lahir"] = (
				row[header_to_idx.get("Place", None)].strip()
				if header_to_idx.get("Place") is not None
				else None
			)

			# Handle Status Pajak values
			status_pajak_val = row[header_to_idx.get("Status Pajak", None)]
			if status_pajak_val is not None:
				status_pajak_val = status_pajak_val.strip()
				employee_data["status_pajak"] = status_pajak_val.replace("/", "")
			else:
				employee_data["status_pajak"] = None

			employee_data["custom_agama"] = (
				row[header_to_idx.get("Agama", None)].strip()
				if header_to_idx.get("Agama") is not None
				else None
			)
			employee_data["npwp"] = (
				row[header_to_idx.get("NPWP", None)].strip()
				if header_to_idx.get("NPWP") is not None
				else None
			)

			gender_val = (
				row[header_to_idx.get("Jenis Kelamin", None)].strip()
				if header_to_idx.get("Jenis Kelamin") is not None
				else None
			)
			employee_data["gender"] = gender_val

			employee_data["current_address"] = (
				row[header_to_idx.get("Domisili", None)].strip()
				if header_to_idx.get("Domisili") is not None
				else None
			)
			employee_data["permanent_address"] = (
				row[header_to_idx.get("Alamat Terbaru", None)].strip()
				if header_to_idx.get("Alamat Terbaru") is not None
				else None
			)

			employee_data["cell_number"] = (
				row[header_to_idx.get("No. HP", None)].strip()
				if header_to_idx.get("No. HP") is not None
				else None
			)

			personal_email_val = (
				row[header_to_idx.get("Email", None)].strip()
				if header_to_idx.get("Email") is not None
				else None
			)

			# Check if email is empty or invalid placeholder
			if not personal_email_val or personal_email_val == "-":
				first_name_clean = employee_data["first_name"].lower().replace(" ", "")
				personal_email_val = f"{first_name_clean}@gmail.com"
				print(f"  -> Email kosong/invalid, diisi otomatis: {personal_email_val}")
			employee_data["personal_email"] = personal_email_val

			if employee_data["personal_email"]:
				employee_data["prefered_contact_email"] = "Personal Email"
			else:
				employee_data["prefered_contact_email"] = None

			employee_data["bank_name"] = (
				row[header_to_idx.get("Bank", None)].strip()
				if header_to_idx.get("Bank") is not None
				else None
			)
			employee_data["bank_ac_no"] = (
				row[header_to_idx.get("No. Rekening", None)].strip()
				if header_to_idx.get("No. Rekening") is not None
				else None
			)

			bpjs_ket_val = (
				row[header_to_idx.get("BPJS Ketenagakerjaan", None)].strip()
				if header_to_idx.get("BPJS Ketenagakerjaan") is not None
				else None
			)
			employee_data["ikut_bpjs_ketenagakerjaan"] = 1 if bpjs_ket_val else 0
			employee_data["bpjs_ketenagakerjaan_id"] = bpjs_ket_val if bpjs_ket_val else None

			bpjs_kes_val = (
				row[header_to_idx.get("BPJS Kesehatan", None)].strip()
				if header_to_idx.get("BPJS Kesehatan") is not None
				else None
			)
			employee_data["ikut_bpjs_kesehatan"] = 1 if bpjs_kes_val else 0
			employee_data["bpjs_kesehatan_id"] = bpjs_kes_val if bpjs_kes_val else None

			education_list = []
			edu_level = (
				row[header_to_idx.get("Pendidikan", None)].strip()
				if header_to_idx.get("Pendidikan") is not None
				else None
			)
			institute = (
				row[header_to_idx.get("Universitas", None)].strip()
				if header_to_idx.get("Universitas") is not None
				else None
			)
			major = (
				row[header_to_idx.get("Jurusan", None)].strip()
				if header_to_idx.get("Jurusan") is not None
				else None
			)

			if edu_level or institute or major:
				education_list.append(
					{
						"doctype": "Employee Education",
						"qualification": edu_level,
						"school_univ": institute,
						"maj_opt_subj": major,
					}
				)
			employee_data["education"] = education_list

			if employee_data["employee_number"] and frappe.db.exists(
				"Employee", {"employee_number": employee_data["employee_number"]}
			):
				print(
					f"Karyawan dengan NIK {employee_data['employee_number']} sudah ada, dilewati (untuk menghindari duplikasi)."
				)
				continue

			try:
				employee_doc = frappe.get_doc(employee_data)
				employee_doc.insert()
				frappe.db.commit()
				print(
					f"Karyawan {employee_data.get('employee_name', 'N/A')} (NIK: {employee_data.get('employee_number', 'N/A')}) berhasil dimigrasi."
				)
			except Exception as e:
				frappe.db.rollback()
				print(
					f"Gagal memigrasi karyawan {employee_data.get('employee_name', 'N/A')} (NIK: {employee_data.get('employee_number', 'N/A')}): {e}"
				)

	print("\nMigrasi data karyawan selesai.")


if __name__ == "__main__":
	migrate_employee_data()
