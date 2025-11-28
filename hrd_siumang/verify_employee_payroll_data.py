import frappe


def verify_employee_payroll_data():
	"""
	Verifies key payroll-related data for a specific employee.
	"""
	frappe.set_user("Administrator")  # Ensure permissions

	employee_id = "HR-EMP-00003"

	print(f"\n--- Memverifikasi Data Payroll Karyawan: {employee_id} ---")

	try:
		# 1. Fetch Employee document
		employee = frappe.get_doc("Employee", employee_id)
		print(f"Nama Karyawan: {employee.employee_name}")
		print(f"Status Pajak: {employee.status_pajak}")
		print(f"Holiday List: {employee.holiday_list}")

		# 2. Check CTC (Cost to Company) - often a field on Employee or Salary Structure Assignment
		# Assuming CTC is a field on Employee for simplicity or we'd look in Salary Structure Assignment
		ctc_value = employee.get("ctc")  # This is a standard ERPNext field
		if ctc_value:
			print(f"CTC (Cost to Company) di Employee: {frappe.format(ctc_value, 'Currency')}")
		else:
			print("CTC di Employee: Tidak disetel atau 0.")

		# 3. Fetch Salary Structure Assignment for relevant period
		print("\n--- Salary Structure Assignment ---")
		ssa_records = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": employee_id, "docstatus": 1},  # Filter for submitted assignments
			fields=["name", "salary_structure", "from_date", "base"],
		)

		if ssa_records:
			for ssa in ssa_records:
				print(f"  Nama SSA: {ssa.name}")
				print(f"  Struktur Gaji: {ssa.salary_structure}")
				print(f"  Berlaku dari: {ssa.from_date}")
				print(f"  Base (dari SSA): {frappe.format(ssa.base, 'Currency')}")
				print(f"  Fixed Amount (dari SSA): {frappe.format(ssa.fixed_amount, 'Currency')}")
		else:
			print("Tidak ada Salary Structure Assignment yang aktif ditemukan untuk karyawan ini.")

		# 4. Fetch Employee Allowance Data
		print("\n--- Employee Allowance Data ---")
		try:
			# Fetch the entire document for Employee Allowance Data
			ea_records = frappe.get_all(
				"Employee Allowance Data",
				filters={"employee": employee_id, "docstatus": 1},  # Filter for submitted allowances
				fields=["name"],  # Just get the name to fetch the full doc
			)
			if ea_records:
				for ea_summary in ea_records:
					ea_doc = frappe.get_doc("Employee Allowance Data", ea_summary.name)
					print(f"  Nama Dokumen Tunjangan: {ea_doc.name}")
					print(f"    - Tunjangan Jabatan: {frappe.format(ea_doc.tunjangan_jabatan, 'Currency')}")
					print(
						f"    - Tunjangan Komunikasi: {frappe.format(ea_doc.tunjangan_komunikasi, 'Currency')}"
					)
					print(f"    - Tunjangan Lain: {frappe.format(ea_doc.tunjangan_lain, 'Currency')}")
					print(
						f"    - Tunjangan Transport: {frappe.format(ea_doc.tunjangan_transport, 'Currency')}"
					)
					print(f"    - Tunjangan Makan: {frappe.format(ea_doc.tunjangan_makan, 'Currency')}")
			else:
				print("Tidak ada Employee Allowance Data yang aktif ditemukan untuk karyawan ini.")
		except Exception as e:
			print(f"❌ Gagal mengambil Employee Allowance Data: {e}")
			frappe.log_error(frappe.get_traceback(), "Gagal Mengambil Employee Allowance Data")

	except frappe.DoesNotExistError:
		print(f"❌ Karyawan dengan ID '{employee_id}' tidak ditemukan.")
	except Exception as e:
		print(f"❌ Gagal memverifikasi data karyawan: {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Verifikasi Data Payroll Karyawan")

	print("---------------------------------------------------\n")
