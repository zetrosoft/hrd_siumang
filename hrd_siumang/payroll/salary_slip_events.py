import frappe

from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21


def calculate_payroll_components(doc, method):
	"""
	DocEvent for Salary Slip before_save.
	Populates all components from the Salary Structure,
	overriding with calculated values (Gaji Pokok, Tunjangan, BPJS, Overtime, PPh 21),
	and setting JKN components to 0. Finally, sets the totals.
	"""
	# Clear existing earnings and deductions to avoid duplicates and ensure fresh population
	doc.set("earnings", [])
	doc.set("deductions", [])

	# 1. Fetch Source Data
	employee_id = doc.employee
	ssa_records = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee_id, "docstatus": 1, "from_date": ["<=", doc.start_date]},
		fields=["name", "salary_structure", "from_date", "base"],
		order_by="from_date desc",
		limit=1,
	)
	if not ssa_records:
		frappe.throw(
			f"Tidak ada Salary Structure Assignment aktif ditemukan untuk Karyawan {employee_id} sebelum {doc.start_date}."
		)
	ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa_records[0].name)
	ea_records = frappe.get_all(
		"Employee Allowance Data", filters={"employee": employee_id, "docstatus": 1}, fields=["name"]
	)
	ea_doc = frappe.get_doc("Employee Allowance Data", ea_records[0].name) if ea_records else None
	salary_structure_doc = frappe.get_doc("Salary Structure", doc.salary_structure)

	# 2. Calculate Base Values and preliminary components
	base_amount = ssa_doc.base
	print("--- DEBUG salary_slip_events ---")
	print(f"base_amount: {base_amount}")

	tunjangan_tetap = 0
	if ea_doc:
		tunjangan_jabatan = ea_doc.tunjangan_jabatan if ea_doc.tunjangan_jabatan else 0
		tunjangan_komunikasi = ea_doc.tunjangan_komunikasi if ea_doc.tunjangan_komunikasi else 0
		tunjangan_tetap += tunjangan_jabatan
		tunjangan_tetap += tunjangan_komunikasi
	print(f"tunjangan_tetap: {tunjangan_tetap}")
	bpjs_base = base_amount + tunjangan_tetap
	print(f"bpjs_base: {bpjs_base}")

	calculated_component_values = {}

	# Populate Earnings
	calculated_component_values["Gaji Pokok"] = base_amount
	if ea_doc:
		calculated_component_values["Tunjangan Jabatan"] = ea_doc.tunjangan_jabatan or 0
		calculated_component_values["Tunjangan Komunikasi"] = ea_doc.tunjangan_komunikasi or 0
		calculated_component_values["Tunjangan Transport"] = ea_doc.tunjangan_transport or 0
		calculated_component_values["Tunjangan Makan"] = ea_doc.tunjangan_makan or 0
		calculated_component_values["Tunjangan Lain"] = ea_doc.tunjangan_lain or 0

	calculated_component_values["JHT Perusahaan"] = round(bpjs_base * 0.037)
	calculated_component_values["JKK Perusahaan"] = round(bpjs_base * 0.0089)
	calculated_component_values["JKM Perusahaan"] = round(bpjs_base * 0.003)
	calculated_component_values["JP Perusahaan"] = round(bpjs_base * 0.02)
	calculated_component_values["JKN Perusahaan"] = 0

	# Calculate Absence Deduction
	absent_days = frappe.db.count(
		"Attendance",
		filters={
			"employee": doc.employee,
			"status": "Absent",
			"attendance_date": ["between", (doc.start_date, doc.end_date)],
		},
	)

	if absent_days > 0:
		gaji_dasar_potongan = (
			bpjs_base  # Menggunakan dasar yang sama dengan BPJS (Gaji Pokok + Tunjangan Tetap)
		)
		working_days_in_month = 25  # Asumsi hari kerja
		gaji_per_hari = gaji_dasar_potongan / working_days_in_month
		potongan_absensi = round(absent_days * gaji_per_hari)

		print(f"DEBUG: Ditemukan {absent_days} hari absen. Potongan: {potongan_absensi}")
		calculated_component_values["Potongan Absensi"] = potongan_absensi
	else:
		calculated_component_values["Potongan Absensi"] = 0

	# --- Populate Deductions (JHT Karyawan, JP Karyawan) ---
	jht_karyawan_val = round(bpjs_base * 0.02)
	jp_karyawan_val = round(bpjs_base * 0.01)
	print(f"JHT Karyawan (dihitung): {jht_karyawan_val}")
	print(f"JP Karyawan (dihitung): {jp_karyawan_val}")
	calculated_component_values["JHT Karyawan"] = jht_karyawan_val
	calculated_component_values["JP Karyawan"] = jp_karyawan_val
	calculated_component_values["JKN Karyawan"] = 0

	# 3. Populate doc.earnings and doc.deductions fully BEFORE PPh 21 calculation
	# Populate doc.earnings
	for comp in salary_structure_doc.earnings:
		amount = calculated_component_values.get(comp.salary_component, 0)
		doc.append("earnings", {"salary_component": comp.salary_component, "amount": amount})

	all_deduction_components = {item.salary_component for item in salary_structure_doc.deductions}
	custom_deduction_components = [
		"JHT Karyawan",
		"JP Karyawan",
		"JKN Karyawan",
		"Potongan Absensi",
		"Potongan Lain-lain",
		"PPh 21",
	]
	for comp in custom_deduction_components:
		all_deduction_components.add(comp)
	company_bpjs_components = [
		"JHT Perusahaan",
		"JKK Perusahaan",
		"JKM Perusahaan",
		"JP Perusahaan",
		"JKN Perusahaan",
	]
	for comp in company_bpjs_components:
		all_deduction_components.add(comp)

	for component_name in sorted(list(all_deduction_components)):
		if component_name in calculated_component_values:
			amount = calculated_component_values.get(component_name, 0)
			doc.append("deductions", {"salary_component": component_name, "amount": amount})

	# Now that doc.earnings and doc.deductions are fully populated, calculate gross_pay and PPh 21
	doc.gross_pay = sum(item.amount for item in doc.earnings)
	overtime_amount = calculate_overtime(doc)
	pph21_amount = calculate_pph21(doc)

	calculated_component_values["Overtime"] = overtime_amount
	calculated_component_values["PPh 21"] = pph21_amount

	# 4. Final Population of earnings and deductions to ensure correct order and all values are included
	doc.set("earnings", [])
	for comp in salary_structure_doc.earnings:
		component_name = comp.salary_component
		amount = calculated_component_values.get(component_name, 0)
		doc.append("earnings", {"salary_component": component_name, "amount": amount})

	doc.set("deductions", [])
	for comp in salary_structure_doc.deductions:
		component_name = comp.salary_component
		amount = calculated_component_values.get(component_name, 0)
		doc.append("deductions", {"salary_component": component_name, "amount": amount})

	# --- Final Totals ---
	doc.gross_pay = sum(item.amount for item in doc.earnings)
	doc.total_deduction = sum(item.amount for item in doc.deductions)
	doc.net_pay = doc.gross_pay - doc.total_deduction

	# DEBUG PPH 21 (frappe.msgprint for UI display)
	frappe.msgprint(f"DEBUG FINAL PPH: Gross Pay untuk PPh 21: {doc.gross_pay}")
	frappe.msgprint(f"DEBUG FINAL PPH: PPh 21 dihitung: {pph21_amount}")
