import frappe
from frappe.utils import nowdate

# ==== KONFIGURASI UTAMA ====

# Tentukan urutan komponen sesuai dengan tampilan slip gaji yang diinginkan
EARNINGS_ORDER = [
	"Gaji Pokok",
	"Tunjangan Jabatan",
	"Tunjangan Komunikasi",
	"Tunjangan Lain",
	"Tunjangan Transport",
	"Tunjangan Makan",
	"Overtime",
	"Rapel",
	"JHT Perusahaan",
	"JKK Perusahaan",
	"JKM Perusahaan",
	"JP Perusahaan",
	"JKN Perusahaan",
]

DEDUCTIONS_ORDER = [
	"Potongan Absensi",
	"Potongan Lain-lain",
	"JHT Karyawan",
	"JP Karyawan",
	"JKN Karyawan",
	"PPh 21",
]

# Daftar semua komponen yang perlu dibuat
ALL_COMPONENTS = {
	"Gaji Pokok": {"type": "Earning", "abbr": "GP", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Tunjangan Jabatan": {"type": "Earning", "abbr": "TJ", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Tunjangan Komunikasi": {"type": "Earning", "abbr": "TKOM", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Tunjangan Lain": {"type": "Earning", "abbr": "TL", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Tunjangan Transport": {"type": "Earning", "abbr": "TTR", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Tunjangan Makan": {"type": "Earning", "abbr": "TM", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Overtime": {"type": "Earning", "abbr": "OT", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Rapel": {"type": "Earning", "abbr": "R", "account": "1111.002 - Kas Besar - SIUMANG"},
	# BPJS Perusahaan (masuk earnings karena merupakan pendapatan tidak langsung bagi karyawan untuk tujuan PPh 21)
	"JHT Perusahaan": {"type": "Earning", "abbr": "JHT-P", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JKK Perusahaan": {"type": "Earning", "abbr": "JKK-P", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JKM Perusahaan": {"type": "Earning", "abbr": "JKM-P", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JP Perusahaan": {"type": "Earning", "abbr": "JP-P", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JKN Perusahaan": {"type": "Earning", "abbr": "JKN-P", "account": "1111.002 - Kas Besar - SIUMANG"},
	# Deductions
	"Potongan Absensi": {"type": "Deduction", "abbr": "PA", "account": "1111.002 - Kas Besar - SIUMANG"},
	"Potongan Lain-lain": {"type": "Deduction", "abbr": "PL", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JHT Karyawan": {"type": "Deduction", "abbr": "JHT-K", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JP Karyawan": {"type": "Deduction", "abbr": "JP-K", "account": "1111.002 - Kas Besar - SIUMANG"},
	"JKN Karyawan": {"type": "Deduction", "abbr": "JKN-K", "account": "1111.002 - Kas Besar - SIUMANG"},
	"PPh 21": {"type": "Deduction", "abbr": "PPH21", "account": "1111.002 - Kas Besar - SIUMANG"},
}


# ==== FUNGSI-FUNGSI HELPER ====


def create_salary_components(dry_run=False):
	"""Membuat semua Salary Component yang didefinisikan di ALL_COMPONENTS jika belum ada."""
	print("\n--- Memulai pembuatan Salary Components (Master) ---")
	for name, data in ALL_COMPONENTS.items():
		if not frappe.db.exists("Salary Component", name):
			if dry_run:
				print(f"[DRY RUN] Akan membuat Salary Component: '{name}'")
				continue

			try:
				doc = frappe.new_doc("Salary Component")
				doc.name = name
				doc.salary_component_name = name
				doc.salary_component = name
				doc.type = data["type"]
				doc.salary_component_abbr = data["abbr"]

				# Append to the 'accounts' child table
				doc.append("accounts", {"company": "PT. SIUMANG TEMAN SUKSES", "account": data["account"]})

				doc.amount_based_on_formula = data.get("amount_based_on_formula", 0)
				doc.is_flexible_benefit = data.get("is_flexible_benefit", 0)
				doc.statistical_component = data.get("statistical_component", 0)
				doc.do_not_include_in_total = data.get("do_not_include_in_total", 0)

				doc.save(ignore_permissions=True)
				print(f"✅ BERHASIL: Salary Component '{name}' dibuat.")
			except Exception as e:
				print(f"❌ GAGAL saat membuat Salary Component '{name}': {e}")
				raise
		else:
			print(f"[INFO] Salary Component '{name}' sudah ada. Melewati.")
	print("--- Selesai (Salary Components) ---")


def create_structures_per_employment_type(dry_run=False):
	"""
	Membuat satu Salary Structure untuk setiap Employment Type yang unik dari karyawan aktif.
	Struktur ini akan menjadi blueprint umum.
	"""
	print("\n--- Memulai pembuatan Salary Structures per Employment Type ---")
	employment_types = frappe.get_all(
		"Employee", filters={"status": "Active"}, fields=["employment_type"], distinct=True
	)

	if not employment_types:
		print("Tidak ada Karyawan aktif dengan Employment Type yang ditemukan.")
		return

	for emp_type in employment_types:
		if not emp_type.employment_type:
			continue

		structure_name = f"Struktur Gaji - {emp_type.employment_type}"
		if frappe.db.exists("Salary Structure", structure_name):
			print(f"[INFO] Salary Structure '{structure_name}' sudah ada. Melewati.")
			continue

		if dry_run:
			print(f"[DRY RUN] Akan membuat Salary Structure: '{structure_name}'")
			continue

		print(f"Membuat Salary Structure untuk '{emp_type.employment_type}'...")
		try:
			ss_doc = frappe.new_doc("Salary Structure")
			ss_doc.name = structure_name
			ss_doc.salary_structure_name = structure_name
			ss_doc.company = "PT. SIUMANG TEMAN SUKSES"
			ss_doc.is_active = "Yes"
			ss_doc.currency = frappe.get_cached_value(
				"Company", "PT. SIUMANG TEMAN SUKSES", "default_currency"
			)

			# Tambahkan earnings sesuai urutan
			for component in EARNINGS_ORDER:
				ss_doc.append("earnings", {"salary_component": component})

			# Tambahkan deductions sesuai urutan
			for component in DEDUCTIONS_ORDER:
				ss_doc.append("deductions", {"salary_component": component})

			ss_doc.save(ignore_permissions=True)
			ss_doc.submit()
			print(f"✅ BERHASIL: Salary Structure '{structure_name}' dibuat dan diserahkan.")

		except Exception as e:
			print(f"❌ GAGAL saat membuat Salary Structure '{structure_name}': {e}")
			raise


def assign_structures_to_employees(dry_run=False):
	"""
	Membuat Salary Structure Assignment untuk semua karyawan aktif
	berdasarkan Employment Type mereka, menggunakan tanggal bergabung sebagai from_date.
	"""
	print("\n--- Memulai pembuatan Salary Structure Assignments ---")
	employees = frappe.get_list(
		"Employee",
		filters={"status": "Active", "company": "PT. SIUMANG TEMAN SUKSES"},
		fields=["name", "employee_name", "employment_type", "ctc", "date_of_joining"],
	)

	if not employees:
		print("Tidak ada karyawan aktif ditemukan.")
		return

	for emp in employees:
		if not emp.employment_type:
			print(f"[WARN] Karyawan '{emp.employee_name}' tidak memiliki Employment Type. Melewati.")
			continue

		structure_name = f"Struktur Gaji - {emp.employment_type}"
		if not frappe.db.exists("Salary Structure", structure_name):
			print(
				f"[WARN] Salary Structure '{structure_name}' untuk '{emp.employee_name}' tidak ditemukan. Melewati karyawan '{emp.employee_name}'."
			)
			continue

		# Periksa Assignment yang sudah ada, dengan mempertimbangkan from_date
		existing_ssa = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": emp.name,
				"docstatus": 1,
				"salary_structure": structure_name,
				"from_date": emp.date_of_joining,
			},
			"name",
		)

		if existing_ssa:
			print(
				f"[INFO] Karyawan '{emp.employee_name}' sudah memiliki Assignment aktif yang cocok. Melewati."
			)
			continue

		if dry_run:
			print(
				f"[DRY RUN] Akan membuat Assignment untuk '{emp.employee_name}' ke struktur '{structure_name}' dari '{emp.date_of_joining}' dengan base '{emp.ctc or 0}'."
			)
			continue

		print(f"Membuat Assignment untuk '{emp.employee_name}'...")
		try:
			ssa_doc = frappe.new_doc("Salary Structure Assignment")
			ssa_doc.employee = emp.name
			ssa_doc.salary_structure = structure_name
			ssa_doc.from_date = emp.date_of_joining if emp.date_of_joining else frappe.utils.today()
			ssa_doc.base = emp.ctc or 0
			ssa_doc.save(ignore_permissions=True)
			ssa_doc.submit()
			print(f"✅ BERHASIL: Assignment untuk '{emp.employee_name}' dibuat.")
		except Exception as e:
			print(f"❌ GAGAL saat membuat Assignment untuk '{emp.employee_name}': {e}")
			frappe.log_error(frappe.get_traceback(), f"Gagal Membuat SSA untuk {emp.employee_name}")

	print("--- Selesai (Salary Structure Assignments) ---")


# ==== FUNGSI EKSEKUSI UTAMA ====


def _run_logic(dry_run):
	mode = "DRY RUN" if dry_run else "LIVE RUN"
	print(f"\n--- Memulai Migrasi Gaji ({mode}) ---")

	frappe.set_user("Administrator")

	# Langkah 1: Buat semua master komponen
	create_salary_components(dry_run=dry_run)

	# Langkah 2: Buat struktur berdasarkan Tipe Karyawan
	create_structures_per_employment_type(dry_run=dry_run)

	# Langkah 3: Tugaskan karyawan ke struktur yang sesuai
	assign_structures_to_employees(dry_run=dry_run)

	if not dry_run:
		frappe.db.commit()
		print("\n--- Migrasi Selesai (LIVE RUN) ---")
	else:
		print("\n--- Simulasi Selesai (DRY RUN) ---")
		print("Tidak ada data yang diubah di database.")


def test_migration():
	"""Jalankan ini untuk simulasi tanpa mengubah data."""
	_run_logic(dry_run=True)


def run_migration():
	"""PERHATIAN: Jalankan ini hanya setelah test_migration() berhasil. Ini akan mengubah data database."""
	_run_logic(dry_run=False)
