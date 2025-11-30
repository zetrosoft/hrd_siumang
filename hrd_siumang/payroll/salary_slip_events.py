import frappe

from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21


def calculate_payroll_components(doc, method):
	"""
	DocEvent for Salary Slip before_save.
	Refactored logic to correctly calculate all components, incorporate Additional Salary,
	and populate child tables in a clean, sequential manner.
	"""
	# Clear existing tables to ensure a fresh calculation
	doc.set("earnings", [])
	doc.set("deductions", [])

	# 1. Fetch Source Data
	employee_id = doc.employee
	ssa = frappe.get_doc("Salary Structure Assignment", {"employee": employee_id, "docstatus": 1})
	if not ssa:
		frappe.throw(f"No active Salary Structure Assignment found for Employee {employee_id}")

	ea_doc = (
		frappe.get_doc("Employee Allowance Data", {"employee": employee_id})
		if frappe.db.exists("Employee Allowance Data", {"employee": employee_id})
		else None
	)
	salary_structure_doc = frappe.get_doc("Salary Structure", doc.salary_structure)

	# --- Dictionaries to hold calculated values ---
	earnings_map = {}
	deductions_map = {}

	# 2. Calculate Base, Allowances, and BPJS Base
	base_amount = ssa.base
	earnings_map["Gaji Pokok"] = base_amount

	tunjangan_tetap = 0
	if ea_doc:
		tunjangan_jabatan = ea_doc.tunjangan_jabatan or 0
		tunjangan_komunikasi = ea_doc.tunjangan_komunikasi or 0
		tunjangan_tetap = tunjangan_jabatan + tunjangan_komunikasi

		earnings_map["Tunjangan Jabatan"] = tunjangan_jabatan
		earnings_map["Tunjangan Komunikasi"] = tunjangan_komunikasi
		earnings_map["Tunjangan Transport"] = ea_doc.tunjangan_transport or 0
		earnings_map["Tunjangan Makan"] = ea_doc.tunjangan_makan or 0
		earnings_map["Tunjangan Lain"] = ea_doc.tunjangan_lain or 0

	bpjs_base = base_amount + tunjangan_tetap

	# BPJS Ditanggung Perusahaan (Earnings)
	earnings_map["JHT Perusahaan"] = round(bpjs_base * 0.037)
	earnings_map["JKK Perusahaan"] = round(bpjs_base * 0.0089)
	earnings_map["JKM Perusahaan"] = round(bpjs_base * 0.003)
	earnings_map["JP Perusahaan"] = round(bpjs_base * 0.02)
	earnings_map["JKN Perusahaan"] = 0  # Sesuai logika lama

	# BPJS Ditanggung Karyawan (Deductions)
	deductions_map["JHT Karyawan"] = round(bpjs_base * 0.02)
	deductions_map["JP Karyawan"] = round(bpjs_base * 0.01)
	deductions_map["JKN Karyawan"] = 0  # Sesuai logika lama

	# 3. Calculate components that depend on other components (Overtime, LWP)
	# Calculate Overtime and add to earnings
	overtime_amount = calculate_overtime(doc)
	earnings_map["Overtime"] = overtime_amount

	# Calculate Absence Deduction (LWP)
	# This runs after the custom absence processing, so any remaining "Absent" are true LWP
	absent_days = frappe.db.count(
		"Attendance",
		{
			"employee": doc.employee,
			"status": "Absent",
			"attendance_date": ["between", (doc.start_date, doc.end_date)],
		},
	)
	if absent_days > 0:
		working_days_in_month = 25  # Assumption
		daily_rate_for_deduction = bpjs_base / working_days_in_month
		deductions_map["Potongan Absensi"] = round(absent_days * daily_rate_for_deduction)
	else:
		deductions_map["Potongan Absensi"] = 0

	# 4. Fetch and Incorporate Additional Salary
	additional_salaries = frappe.get_all(
		"Additional Salary",
		filters={
			"employee": doc.employee,
			"payroll_date": ["between", (doc.start_date, doc.end_date)],
			"docstatus": 1,
		},
		fields=["salary_component", "amount", "type"],
	)

	for ad_sal in additional_salaries:
		if ad_sal.type == "Earning":
			earnings_map[ad_sal.salary_component] = (
				earnings_map.get(ad_sal.salary_component, 0) + ad_sal.amount
			)
		elif ad_sal.type == "Deduction":
			deductions_map[ad_sal.salary_component] = (
				deductions_map.get(ad_sal.salary_component, 0) + ad_sal.amount
			)

	# 5. Calculate Gross Pay and then PPh 21
	doc.gross_pay = sum(earnings_map.values())
	pph21_amount = calculate_pph21(doc)
	deductions_map["PPh 21"] = pph21_amount

	# 6. Final Population of child tables, respecting the order in Salary Structure
	for comp_row in salary_structure_doc.earnings:
		amount = earnings_map.get(comp_row.salary_component, 0)
		if amount or comp_row.salary_component in earnings_map:  # Only add if value exists
			doc.append("earnings", {"salary_component": comp_row.salary_component, "amount": amount})

	for comp_row in salary_structure_doc.deductions:
		amount = deductions_map.get(comp_row.salary_component, 0)
		if amount or comp_row.salary_component in deductions_map:  # Only add if value exists
			doc.append("deductions", {"salary_component": comp_row.salary_component, "amount": amount})

	# Add any ad-hoc deductions that were not in the structure
	for comp, amount in deductions_map.items():
		if not any(d.salary_component == comp for d in doc.deductions):
			doc.append("deductions", {"salary_component": comp, "amount": amount})

	# 7. Set Final Totals
	doc.gross_pay = sum(e.amount for e in doc.earnings)
	doc.total_deduction = sum(d.amount for d in doc.deductions)
	doc.net_pay = doc.gross_pay - doc.total_deduction
