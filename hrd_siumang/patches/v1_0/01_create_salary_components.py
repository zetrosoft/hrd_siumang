# Patch 1: Membuat Salary Components
import frappe


def execute():
	"""Membuat semua record Salary Component jika belum ada."""
	frappe.set_user("Administrator")
	print("Memulai Patch: Membuat Salary Components...")
	company_name = "PT. SIUMANG TEMAN SUKSES"  # Pastikan nama Company ini benar!

	salary_components = [
		# Earnings
		{"name": "Gaji Pokok", "type": "Earning", "abbr": "GP"},
		{"name": "Tunjangan Jabatan", "type": "Earning", "abbr": "TJ"},
		{"name": "Tunjangan Komunikasi", "type": "Earning", "abbr": "TKOM"},
		{"name": "Tunjangan Lain", "type": "Earning", "abbr": "TL"},
		{"name": "Tunjangan Transport", "type": "Earning", "abbr": "TTR"},
		{"name": "Tunjangan Makan", "type": "Earning", "abbr": "TM"},
		{
			"name": "Overtime",
			"type": "Earning",
			"abbr": "OT",
			"formula": "hrd_siumang.payroll.payroll_utils.calculate_overtime(doc)",
		},
		{"name": "Rapel", "type": "Earning", "abbr": "R"},
		{"name": "Tax Allowance", "type": "Earning", "abbr": "TAX-A"},
		{
			"name": "JHT Perusahaan",
			"type": "Earning",
			"abbr": "JHT-P",
			"formula": "base * 0.037",
			"is_statutory_component": 1,
		},
		{
			"name": "JKK Perusahaan",
			"type": "Earning",
			"abbr": "JKK-P",
			"formula": "base * 0.0089",
			"is_statutory_component": 1,
		},
		{
			"name": "JKM Perusahaan",
			"type": "Earning",
			"abbr": "JKM-P",
			"formula": "base * 0.003",
			"is_statutory_component": 1,
		},
		{
			"name": "JP Perusahaan",
			"type": "Earning",
			"abbr": "JP-P",
			"formula": "base * 0.02",
			"is_statutory_component": 1,
		},
		{
			"name": "JKN Perusahaan",
			"type": "Earning",
			"abbr": "JKN-P",
			"formula": "base * 0.04",
			"is_statutory_component": 1,
		},
		# Deductions
		{"name": "Potongan Absensi", "type": "Deduction", "abbr": "PA"},
		{"name": "Potongan Lain-lain", "type": "Deduction", "abbr": "PL"},
		{
			"name": "JHT Karyawan",
			"type": "Deduction",
			"abbr": "JHT-K",
			"formula": "base * 0.02",
			"is_statutory_component": 1,
		},
		{
			"name": "JP Karyawan",
			"type": "Deduction",
			"abbr": "JP-K",
			"formula": "base * 0.01",
			"is_statutory_component": 1,
		},
		{
			"name": "JKN Karyawan",
			"type": "Deduction",
			"abbr": "JKN-K",
			"formula": "base * 0.01",
			"is_statutory_component": 1,
		},
		{"name": "Tax PPh21", "type": "Deduction", "abbr": "TAX-P21", "formula": "calculate_pph21(doc)"},
	]

	# Blok rename dihapus (sudah kita sepakati ini bermasalah)

	for sc_data in salary_components:
		if not frappe.db.exists("Salary Component", sc_data["name"]):
			# --- START: Pembentukan Dokumen Baru ---
			doc = frappe.new_doc("Salary Component")

			# 1. FIELD MANDATORY: Name Source (Sumber untuk Autoname)
			doc.salary_component = sc_data["name"]

			# 2. FIELD MANDATORY: Type
			doc.type = sc_data["type"]

			# 3. FIELD MANDATORY: Abbreviation
			doc.salary_component_abbr = sc_data.get("abbr")  # Pastikan ini tidak None

			# --- FIELD WAJIB DI HOOK/LOGIC (Asumsi) ---
			doc.company = company_name

			# Field Check (Boolean) wajib disetel untuk lolos validasi
			if sc_data.get("formula"):
				doc.amount_based_on_formula = 1
				doc.formula = sc_data.get("formula")
			else:
				doc.amount_based_on_formula = 0

			doc.is_flexible_benefit = 0
			doc.is_tax_applicable = 0
			doc.is_statutory_component = sc_data.get("is_statutory_component", 0)
			doc.is_paid_against_tax = 0  # Seringkali required

			# Tidak ada penyetelan doc.name di sini. Biarkan Frappe yang menamai dari salary_component_name.
			doc.save(ignore_permissions=True)
			print(f"✅ BERHASIL: Salary Component '{sc_data['name']}' dibuat.")
		else:
			print(f"[INFO] Salary Component '{sc_data['name']}' sudah ada.")

	frappe.db.commit()
	print("Patch 'create_salary_components' selesai.")
