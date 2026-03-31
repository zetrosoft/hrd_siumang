import frappe
from frappe import _
from frappe.query_builder import Order
from frappe.utils import getdate

from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21


def _calculate_borongan_for_employee(employee, start_date, end_date):
	"""Helper function to calculate total piecework earnings for a single employee."""
	total_earnings = 0

	# --- 1. Get Individual Earnings ---
	individual_earnings = frappe.db.sql(
		"""
		SELECT SUM(d.total_harga_item)
		FROM `tabDetail Hasil Borongan` d
		JOIN `tabInput Hasil Borongan` p ON d.parent = p.name
		WHERE d.tipe_penerima_tugas = 'Individu'
		AND d.karyawan = %(employee)s
		AND p.docstatus = 1
		AND p.tanggal BETWEEN %(start_date)s AND %(end_date)s
	""",
		{"employee": employee, "start_date": start_date, "end_date": end_date},
	)
	if individual_earnings and individual_earnings[0][0]:
		total_earnings += individual_earnings[0][0]

	# --- 2. Get Team Earnings ---
	# Find all teams the employee is a member of
	member_of_teams = frappe.get_all("Anggota Tim Borongan", filters={"karyawan": employee}, pluck="parent")

	if not member_of_teams:
		return total_earnings

	# Get all team-based work within the period
	team_based_work = frappe.get_all(
		"Detail Hasil Borongan",
		fields=["parent", "karyawan", "total_harga_item"],
		filters={
			"tipe_penerima_tugas": "Tim",
			"karyawan": ["in", member_of_teams],
			"parenttype": "Input Hasil Borongan",
		},
	)

	if not team_based_work:
		return total_earnings

	# Pre-fetch parent dates
	parent_docs = frappe.get_all(
		"Input Hasil Borongan",
		filters={
			"name": ("in", [d.parent for d in team_based_work]),
			"docstatus": 1,
			"tanggal": ("between", [start_date, end_date]),
		},
		fields=["name", "tanggal"],
	)
	valid_parents = {doc.name: doc.tanggal for doc in parent_docs}

	# Pre-fetch team member counts
	team_member_counts = {}
	for team_name in member_of_teams:
		count = frappe.db.count("Anggota Tim Borongan", {"parent": team_name, "parenttype": "Tim Borongan"})
		team_member_counts[team_name] = count if count > 0 else 1

	for work in team_based_work:
		if work.parent in valid_parents:
			team_name = work.karyawan
			num_members = team_member_counts.get(team_name, 1)
			employee_share = work.total_harga_item / num_members
			total_earnings += employee_share

	return total_earnings


def calculate_payroll_components(doc, method):
	"""
	DocEvent for Salary Slip before_save.
	Calculates all salary components based on custom logic defined in hrd_siumang app.
	This now includes a special path for 'Struktur Gaji - Harian'.
	"""
	# --- Special Path for Incentive Salary Slips ---
	# Skip all calculations if this slip is generated from Employee Incentive
	if getattr(doc, "custom_is_incentive_slip", None):
		return

	if doc.payroll_entry:
		is_incentive_pe = frappe.db.get_value("Payroll Entry", doc.payroll_entry, "custom_incentive_employee_incentive")
		if is_incentive_pe:
			return

	# --- Special Path for Daily/Borongan Workers ---
	if doc.salary_structure == "Struktur Gaji - Harian":
		# Calculate total borongan earnings for the period
		total_borongan = _calculate_borongan_for_employee(doc.employee, doc.start_date, doc.end_date)

		new_earnings = []
		new_deductions = []

		salary_structure_doc = frappe.get_doc("Salary Structure", doc.salary_structure)

		# Populate earnings, but override Gaji Pokok and zero out others
		for comp_row in salary_structure_doc.earnings:
			amount = 0
			if comp_row.salary_component == "Gaji Pokok":
				amount = total_borongan

			new_earnings.append(
				{
					"doctype": "Salary Detail",
					"salary_component": comp_row.salary_component,
					"amount": amount,
				}
			)

		# Populate deductions and zero them out
		for comp_row in salary_structure_doc.deductions:
			new_deductions.append(
				{
					"doctype": "Salary Detail",
					"salary_component": comp_row.salary_component,
					"amount": 0,
				}
			)

		doc.set("earnings", new_earnings)
		doc.set("deductions", new_deductions)

		# Recalculate final amounts
		doc.gross_pay = total_borongan
		doc.total_deduction = 0
		doc.net_pay = total_borongan

		return  # IMPORTANT: Stop execution to prevent regular calculation from running

	# --- Regular Monthly Calculation Logic (Original Code) ---
	# Guard clause to prevent recalculation on submitted documents
	if doc.docstatus > 0 or doc.get("__submitting") or doc.flags.in_submit:
		return

	try:
		# --- Find and set Salary Structure if not present ---
		if not doc.salary_structure:
			joining_date = frappe.get_cached_value("Employee", doc.employee, "date_of_joining")

			ss = frappe.qb.DocType("Salary Structure")
			ssa = frappe.qb.DocType("Salary Structure Assignment")

			query = (
				frappe.qb.from_(ssa)
				.join(ss)
				.on(ssa.salary_structure == ss.name)
				.select(ssa.salary_structure)
				.where(
					(ssa.docstatus == 1)
					& (ss.docstatus == 1)
					& (ss.is_active == "Yes")
					& (ssa.employee == doc.employee)
					& (
						(ssa.from_date <= doc.start_date)
						| (ssa.from_date <= doc.end_date)
						| (ssa.from_date <= joining_date if joining_date else getdate())
					)
				)
				.orderby(ssa.from_date, order=Order.desc)
				.limit(1)
			)

			if not doc.salary_slip_based_on_timesheet and doc.payroll_frequency:
				query = query.where(ss.payroll_frequency == doc.payroll_frequency)

			st_name = query.run(as_list=True)

			if st_name and st_name[0]:
				doc.salary_structure = st_name[0][0]
			else:
				frappe.throw(
					_(
						"No active or default Salary Structure found for employee {0} for the given dates"
					).format(doc.employee)
				)

		# --- Start of Calculation Logic ---
		new_earnings = []
		new_deductions = []
		earnings_map = {}
		deductions_map = {}

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

		base_amount = ssa.base
		earnings_map["Gaji Pokok"] = base_amount

		tunjangan_tetap = 0
		if ea_doc:
			tunjangan_jabatan = ea_doc.tunjangan_jabatan or 0
			tunjangan_komunikasi = ea_doc.tunjangan_komunikasi or 0
			tunjangan_tetap = tunjangan_jabatan + tunjangan_komunikasi
			earnings_map.update(
				{
					"Tj. Jabatan": tunjangan_jabatan,
					"Tj. Komunikasi": tunjangan_komunikasi,
					"Tj. Transport": ea_doc.tunjangan_transport or 0,
					"Tj. Makan": ea_doc.tunjangan_makan or 0,
					"Tj. Lain": ea_doc.tunjangan_lain or 0,
				}
			)

		bpjs_base = base_amount + tunjangan_tetap
		earnings_map.update(
			{
				"JHT Perusahaan 3,7%": round(bpjs_base * 0.037),
				"JKK 0,89%": round(bpjs_base * 0.0089),
				"JKM 0,3%": round(bpjs_base * 0.003),
				"JP Perusahaan 2%": round(bpjs_base * 0.02),
				"JKN Perusahaan 4%": 0,
			}
		)
		deductions_map.update(
			{
				"JHT Perusahaan 3,7%": earnings_map["JHT Perusahaan 3,7%"],
				"JKK 0,89%": earnings_map["JKK 0,89%"],
				"JKM 0,3%": earnings_map["JKM 0,3%"],
				"JP Perusahaan 2%": earnings_map["JP Perusahaan 2%"],
				"JKN Perusahaan 4%": earnings_map["JKN Perusahaan 4%"],
				"JHT Karyawan 2%": round(bpjs_base * 0.02),
				"JP Karyawan 1%": round(bpjs_base * 0.01),
				"JKN Karyawan 1%": 0,
			}
		)

		earnings_map["Overtime"] = calculate_overtime(doc)

		absent_days = frappe.db.count(
			"Attendance",
			{
				"employee": doc.employee,
				"status": "Absent",
				"attendance_date": ["between", (doc.start_date, doc.end_date)],
			},
		)
		if absent_days > 0:
			deductions_map["Absensi"] = round((bpjs_base / 25) * absent_days)
		else:
			deductions_map["Absensi"] = 0

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

		gross_pay_temp = sum(earnings_map.values())
		doc.gross_pay = gross_pay_temp
		deductions_map["Tax"] = calculate_pph21(doc)

		for comp_row in salary_structure_doc.earnings:
			amount = earnings_map.get(comp_row.salary_component, 0)
			sal_comp_doc = frappe.get_doc("Salary Component", comp_row.salary_component)
			if not sal_comp_doc.remove_if_zero_valued or amount > 0:
				new_earnings.append(
					{
						"doctype": "Salary Detail",
						"salary_component": comp_row.salary_component,
						"amount": amount,
					}
				)

		for comp_row in salary_structure_doc.deductions:
			amount = deductions_map.get(comp_row.salary_component, 0)
			sal_comp_doc = frappe.get_doc("Salary Component", comp_row.salary_component)
			if not sal_comp_doc.remove_if_zero_valued or amount > 0:
				new_deductions.append(
					{
						"doctype": "Salary Detail",
						"salary_component": comp_row.salary_component,
						"amount": amount,
					}
				)

		doc.set("earnings", new_earnings)
		doc.set("deductions", new_deductions)

		doc.gross_pay = sum(e.get("amount") for e in new_earnings)
		doc.total_deduction = sum(d.get("amount") for d in new_deductions)
		doc.net_pay = doc.gross_pay - doc.total_deduction

	except Exception as e:
		frappe.log_error(
			f"FATAL ERROR in hrd_siumang calculate_payroll_components: {e}", "HRD Siumang Calculation"
		)
		raise
