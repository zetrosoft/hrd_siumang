import frappe


def execute():
	"""
	Patch v2.0 Final: Membersihkan total semua konfigurasi dan transaksi payroll lama,
	lalu membangun ulang dari awal dengan Salary Structure terpisah untuk setiap Tipe Kepegawaian
	dan penugasan cerdas berdasarkan CTC.
	"""
	frappe.set_user("Administrator")
	print("Memulai Patch v2.0 (Final): Pembangunan Ulang Konfigurasi Payroll...")

	# ==========================================================================
	# FASE 1: PEMBERSIHAN MENYELURUH DATA LAMA
	# ==========================================================================
	print("\n--- FASE 1: PEMBERSIHAN DATA LAMA ---")

	# 1. Menghapus Payroll Entry dan Salary Slip lama
	print("Menghapus Payroll Entry dan Salary Slip lama...")
	frappe.db.delete("Payroll Entry")
	frappe.db.delete("Salary Slip")

	# 2. Menghapus Konfigurasi Gaji Lama
	print("Menghapus Salary Structure Assignment, Salary Structure, dan Salary Component lama...")

	# Hapus Assignment
	frappe.db.sql("DELETE FROM `tabSalary Structure Assignment`")

	# Hapus Salary Structure
	old_structures = frappe.get_all("Salary Structure")  # Hapus semua struktur lama
	for struct in old_structures:
		struct_name = struct.name
		try:
			doc = frappe.get_doc("Salary Structure", struct_name)
			# Jika statusnya submitted (1), batalkan dulu
			if doc.docstatus == 1:
				doc.cancel()
				print(f"   - Salary Structure '{struct_name}' (Submitted) dibatalkan.")

			# Sekarang hapus dokumen (baik yang aslinya draft/0 atau sudah dicancel/2)
			frappe.delete_doc("Salary Structure", struct_name, force=True, ignore_permissions=True)
			print(f"   - Salary Structure '{struct_name}' dihapus.")
		except Exception as e:
			print(f"   ❌ GAGAL memproses Salary Structure '{struct_name}': {e}")

			# Hapus SEMUA Salary Component yang ada untuk memastikan kebersihan total
			all_existing_components = frappe.get_all("Salary Component", pluck="name")
			if all_existing_components:
				print(f"Menemukan {len(all_existing_components)} Salary Component lama yang akan dihapus...")
				for comp_name in all_existing_components:
					try:
						# Coba hapus dengan ORM dulu untuk membersihkan child table secara elegan
						doc_to_delete = frappe.get_doc("Salary Component", comp_name)
						doc_to_delete.set("accounts", [])  # Membersihkan child table 'accounts'
						frappe.delete_doc("Salary Component", comp_name, force=True, ignore_permissions=True)
						print(f"   - Salary Component '{comp_name}' dihapus via ORM.")
					except Exception as e:
						print(f"   - GAGAL menghapus '{comp_name}' via ORM: {e}")
						# Jika ORM gagal, fallback ke penghapusan SQL langsung (lebih agresif)
						try:
							frappe.db.sql(
								"DELETE FROM `tabSalary Component Account` WHERE parent=%s", comp_name
							)
							frappe.db.sql("DELETE FROM `tabSalary Component` WHERE name=%s", comp_name)
							frappe.db.commit()  # Commit penghapusan SQL ini
							print(f"   - Salary Component '{comp_name}' dihapus via SQL (fallback).")
						except Exception as sql_e:
							print(
								f"   - GAGAL TOTAL menghapus '{comp_name}' (SQL fallback juga gagal): {sql_e}"
							)
			else:
				print("Tidak ada Salary Component lama yang ditemukan.")
	frappe.db.commit()
	print("✅ FASE 1 Selesai: Semua data payroll lama telah dibersihkan.")

	# ==========================================================================
	# FASE 2: PEMBANGUNAN ULANG KONFIGURASI BARU
	# ==========================================================================
	print("\n--- FASE 2: PEMBANGUNAN ULANG KONFIGURASI ---")

	company_name = "PT. SIUMANG TEMAN SUKSES"

	# Akun-akun yang telah disepakati (Disesuaikan dengan COA Siumang yang aktif)
	acc_beban_gaji = "6-20002 - Beban Gaji Karyawan - SIUMANG"
	acc_beban_tunjangan = "6-20002 - Beban Gaji Karyawan - SIUMANG"
	acc_beban_iuran = "6-20003 - BPJS & Asuransi - SIUMANG"
	acc_hutang_pajak_bpjs = "2-20005 - Utang Pajak - PPh 21 - SIUMANG"

	# Definisi komponen TANPA formula
	salary_components_data = [
		# Pendapatan (Earnings) - Diurutkan sesuai slip gaji
		{"name": "Gaji Pokok", "type": "Earning", "abbr": "GP", "account": acc_beban_gaji},
		{"name": "Tj. Jabatan", "type": "Earning", "abbr": "TJ", "account": acc_beban_tunjangan},
		{"name": "Tj. Komunikasi", "type": "Earning", "abbr": "TKOM", "account": acc_beban_tunjangan},
		{"name": "Tj. Lain", "type": "Earning", "abbr": "TL", "account": acc_beban_tunjangan},
		{"name": "Tj. Transport", "type": "Earning", "abbr": "TTR", "account": acc_beban_tunjangan},
		{"name": "Tj. Makan", "type": "Earning", "abbr": "TM", "account": acc_beban_tunjangan},
		{"name": "Overtime", "type": "Earning", "abbr": "OT", "account": acc_beban_gaji},
		{"name": "Rapel", "type": "Earning", "abbr": "R", "account": acc_beban_gaji},
		{"name": "JHT Perusahaan 3,7%", "type": "Earning", "abbr": "JHT-P", "account": acc_beban_iuran},
		{"name": "JKK 0,89%", "type": "Earning", "abbr": "JKK-P", "account": acc_beban_iuran},
		{"name": "JKM 0,3%", "type": "Earning", "abbr": "JKM-P", "account": acc_beban_iuran},
		{"name": "JP Perusahaan 2%", "type": "Earning", "abbr": "JP-P", "account": acc_beban_iuran},
		{"name": "JKN Perusahaan 4%", "type": "Earning", "abbr": "JKN-P", "account": acc_beban_iuran},
		{"name": "Tax Allowance", "type": "Earning", "abbr": "TAX-A", "account": acc_beban_tunjangan},
		# Potongan (Deductions) - Diurutkan sesuai slip gaji
		{"name": "Absensi", "type": "Deduction", "abbr": "PA", "account": acc_beban_gaji},
		{"name": "Lain-lain", "type": "Deduction", "abbr": "PL", "account": acc_beban_gaji},
		{
			"name": "JHT Perusahaan 3,7%",
			"type": "Deduction",
			"abbr": "JHT-P-D",
			"account": acc_hutang_pajak_bpjs,
		},  # Komponen Potongan baru
		{"name": "JHT Karyawan 2%", "type": "Deduction", "abbr": "JHT-K", "account": acc_hutang_pajak_bpjs},
		{
			"name": "JKK 0,89%",
			"type": "Deduction",
			"abbr": "JKK-P-D",
			"account": acc_hutang_pajak_bpjs,
		},  # Komponen Potongan baru
		{
			"name": "JKM 0,3%",
			"type": "Deduction",
			"abbr": "JKM-P-D",
			"account": acc_hutang_pajak_bpjs,
		},  # Komponen Potongan baru
		{
			"name": "JP Perusahaan 2%",
			"type": "Deduction",
			"abbr": "JP-P-D",
			"account": acc_hutang_pajak_bpjs,
		},  # Komponen Potongan baru
		{"name": "JP Karyawan 1%", "type": "Deduction", "abbr": "JP-K", "account": acc_hutang_pajak_bpjs},
		{
			"name": "JKN Perusahaan 4%",
			"type": "Deduction",
			"abbr": "JKN-P-D",
			"account": acc_hutang_pajak_bpjs,
		},  # Komponen Potongan baru
		{"name": "JKN Karyawan 1%", "type": "Deduction", "abbr": "JKN-K", "account": acc_hutang_pajak_bpjs},
		{"name": "Tax", "type": "Deduction", "abbr": "PPH21", "account": acc_hutang_pajak_bpjs},
	]

	print("Membuat ulang/Memperbarui Salary Components dengan akun yang benar...")
	created_component_names = []

	# Daftar komponen yang tergantung pada hari kerja
	components_with_payment_days = ["Gaji Pokok", "Tunjangan Transport", "Tunjangan Makan", "Tunjangan Lain"]

	for sc_data in salary_components_data:
		comp_name = sc_data["name"]

		# --- Check if Salary Component already exists ---
		if frappe.db.exists("Salary Component", comp_name):
			doc = frappe.get_doc("Salary Component", comp_name)
			print(f"   - Salary Component '{comp_name}' sudah ada, memperbarui...")
		else:
			doc = frappe.new_doc("Salary Component")
			doc.salary_component = comp_name  # For new docs, set name here
			print(f"   - Membuat baru Salary Component '{comp_name}'...")

		doc.type = sc_data["type"]
		doc.salary_component_abbr = sc_data.get("abbr")
		doc.amount_based_on_formula = 0
		doc.remove_if_zero_valued = 0  # Menggunakan field yang benar

		if sc_data["type"] == "Earning":
			doc.depends_on_payment_days = 1 if comp_name in components_with_payment_days else 0
		else:
			doc.depends_on_payment_days = 0

		# Clear existing accounts and append new ones (to handle updates properly)
		doc.set("accounts", [])
		doc.append("accounts", {"company": company_name, "account": sc_data.get("account")})

		# Gunakan .save() untuk kedua skenario (baru dan update), submit_on_insert juga untuk konsistensi
		doc.save(ignore_permissions=True)

		created_component_names.append(comp_name)

		dopd_status = doc.depends_on_payment_days
		dinit_status = doc.remove_if_zero_valued
		print(
			f"   - Komponen '{comp_name}' dibuat/diperbarui: Depends on Payment Days={dopd_status}, Remove if Zero Valued={dinit_status}"
		)

	frappe.db.commit()
	print("\n✅ Daftar Salary Component yang berhasil dibuat/diperbarui ulang:")
	for name in created_component_names:
		print(f"   - {name}")

	# --- Membuat Salary Structure per Tipe Kepegawaian ---
	employment_types = frappe.get_all("Employment Type", pluck="name")
	if not employment_types:
		frappe.throw(
			"Tidak ada 'Employment Type' yang ditemukan di sistem. Harap buat terlebih dahulu (Contoh: Tetap, Kontrak)."
		)

	print("\nMembuat ulang Salary Structure per Tipe Kepegawaian...")
	created_structures = {}
	for emp_type in employment_types:
		struct_name = f"Struktur Gaji - {emp_type}"
		print(f"   - Memproses '{struct_name}'...")

		# Hanya membuat structure dan mengisi nama komponen, tanpa logika tambahan
		if not frappe.db.exists("Salary Structure", struct_name):
			struct_doc = frappe.new_doc("Salary Structure")
			struct_doc.name = struct_name
			struct_doc.company = company_name
			struct_doc.is_active = "Yes"
			struct_doc.payroll_frequency = "Monthly"

			for sc_data in salary_components_data:
				if sc_data["type"] == "Earning":
					struct_doc.append("earnings", {"salary_component": sc_data["name"]})
				else:
					struct_doc.append("deductions", {"salary_component": sc_data["name"]})

			struct_doc.insert(ignore_permissions=True)
			struct_doc.submit()
			created_structures[emp_type] = struct_name
		else:
			# Jika sudah ada, cukup tambahkan ke daftar
			created_structures[emp_type] = struct_name

	frappe.db.commit()
	print("✅ Semua Salary Structure per Tipe Kepegawaian berhasil dibuat ulang.")

	# ==========================================================================
	# FASE 3: ASSIGNMENT STRUKTUR GAJI SECARA CERDAS
	# ==========================================================================
	print("\n--- FASE 3: ASSIGNMENT STRUKTUR GAJI ---")

	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "company": company_name},
		fields=["name", "employee_name", "ctc", "employment_type", "date_of_joining"],
	)

	if not employees:
		print("⚠️  [PERINGATAN] Tidak ada karyawan aktif yang ditemukan untuk perusahaan ini.")
	else:
		for emp in employees:
			ctc = frappe.utils.flt(emp.get("ctc") or 0)
			emp_type = emp.get("employment_type")
			date_of_joining = emp.get("date_of_joining")

			# Validasi kelengkapan data
			if not emp_type:
				print(f"   [INFO] DILEWATI: {emp.employee_name} tidak memiliki 'Employment Type'.")
				continue
			if not date_of_joining:
				print(f"   [INFO] DILEWATI: {emp.employee_name} tidak memiliki 'Date of Joining'.")
				continue

			# Cari Struktur Gaji yang sesuai
			struct_to_assign = f"Struktur Gaji - {emp_type}"
			if not frappe.db.exists("Salary Structure", struct_to_assign):
				print(f"   [INFO] DILEWATI: Tidak ditemukan Salary Structure '{struct_to_assign}' ({emp.employee_name}).")
				continue

			try:
				assignment = frappe.new_doc("Salary Structure Assignment")
				assignment.employee = emp.name
				assignment.salary_structure = struct_to_assign
				assignment.from_date = date_of_joining
				assignment.base_payroll_payable_account = "2-20002 - Utang Gaji - SIUMANG"
				assignment.payroll_payable_account = "2-20002 - Utang Gaji - SIUMANG"
				assignment.company = company_name
				assignment.base = ctc
				
				assignment.insert(ignore_permissions=True)
				assignment.submit()
				print(
					f"   ✅ Berhasil assign '{struct_to_assign}' ke {emp.employee_name} (From: {date_of_joining}, Amount: {ctc})"
				)
			except Exception as e:
				print(f"   ❌ GAGAL assign ke {emp.employee_name}: {e}")

	frappe.db.commit()
	print("✅ FASE 3 Selesai: Assignment struktur gaji selesai.")
	print("\nPatch v2.0 selesai dieksekusi.")
