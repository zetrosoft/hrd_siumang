# Patch 2: Membuat Salary Structures per Grup (FIXED)
import frappe
from frappe.utils import nowdate


def get_component_formula(component_name):
	"""Mengambil formula dan status amount_based_on_formula dari Salary Component."""
	details = frappe.db.get_value(
		"Salary Component", component_name, ["amount_based_on_formula", "formula"], as_dict=True
	)
	if details:
		# Mengembalikan status formula (0 atau 1) dan teks formula (atau string kosong)
		return details.get("amount_based_on_formula", 0), details.get("formula", "")
	return 0, ""


def execute():
	"""Membuat satu Salary Structure untuk setiap Employment Type."""
	frappe.set_user("Administrator")
	print("Memulai Patch: Membuat Salary Structures per Grup...")

	employment_types = [d.name for d in frappe.get_all("Employment Type", fields=["name"])]
	if not employment_types:
		print("⚠️ PERINGATAN: Tidak ada 'Employment Type' ditemukan di sistem. Patch dilewati.")
		return

	# Definisikan urutan komponen pendapatan dan potongan secara eksplisit
	# PASTIKAN NAMA KOMPONEN INI SAMA DENGAN YANG DIBUAT DI PATCH 01!
	earnings_in_order = [
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
		"Tax Allowance",
	]
	deductions_in_order = [
		"Potongan Absensi",
		"Potongan Lain-lain",
		"JHT Karyawan",
		"JP Karyawan",
		"JKN Karyawan",
		"Tax PPh21",  # Diubah dari "Tax" ke "Tax PPh21" agar konsisten
	]

	for emp_type in employment_types:
		structure_name = f"Struktur Gaji - {emp_type}"
		if not frappe.db.exists("Salary Structure", structure_name):
			ss = frappe.new_doc("Salary Structure")

			# --- Perbaikan Penamaan (Berdasarkan Klarifikasi Anda) ---
			ss.name = structure_name  # Menggunakan 'name'

			ss.company = "PT. SIUMANG TEMAN SUKSES"
			ss.is_active = "Yes"
			ss.payroll_payable_account = "2131.001 - Biaya Yang Akan di Bayar - SIUMANG"
			ss.currency = frappe.get_cached_value("Company", "PT. SIUMANG TEMAN SUKSES", "default_currency")

			# --- EARNINGS: Menyalin Formula ---
			for comp in earnings_in_order:
				is_formula, formula_text = get_component_formula(comp)
				ss.append(
					"earnings",
					{
						"salary_component": comp,
						"amount_based_on_formula": is_formula,
						"formula": formula_text,  # Menyalin formula
					},
				)

			# --- DEDUCTIONS: Menyalin Formula ---
			for comp in deductions_in_order:
				is_formula, formula_text = get_component_formula(comp)
				ss.append(
					"deductions",
					{
						"salary_component": comp,
						"amount_based_on_formula": is_formula,
						"formula": formula_text,  # Menyalin formula
					},
				)

			ss.save(ignore_permissions=True)
			ss.submit()
			print(f"✅ BERHASIL: Salary Structure '{structure_name}' dibuat dan disubmit.")
		else:
			print(f"[INFO] Salary Structure '{structure_name}' sudah ada.")

	frappe.db.commit()
	print("Patch 'create_salary_structures' selesai.")
