import os  # Tambahkan import ini
from datetime import datetime  # Tambahkan import ini

import frappe

from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21


# Fungsi debug kustom untuk menulis ke file
def _custom_debug_log(message):
	log_file_path = "/Users/user/Projects/custom-siumang/payroll_debug.log"
	try:
		with open(log_file_path, "a") as f:
			f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}] {message}\n")
	except Exception as e:
		# Fallback ke frappe.log_error jika gagal menulis ke file
		frappe.log_error(f"Failed to write to custom debug log: {e}", "Custom Debug Log Error")
		frappe.log_error(message, "Custom Debug Message")


def calculate_payroll_components(doc, method):
	# PROTEKSI TINGKAT TINGGI:
	# 1. Cek jika flag 'in_submit' sedang aktif di core document
	# 2. Cek docstatus
	# 3. Cek jika proses datang dari Payroll Entry (mass submit)
	if doc.docstatus > 0 or doc.get("__submitting") or doc.flags.in_submit:
		_custom_debug_log(
			f"DEBUG SALARY_SLIP_EVENTS: [STRICT SKIP] {doc.name} sedang proses SUBMIT. Angka dikunci."
		)
		return

	try:
		# --- Lists sementara untuk menampung hasil kalkulasi ---
		new_earnings = []
		new_deductions = []
		earnings_map = {}
		deductions_map = {}

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
		_custom_debug_log(f"DEBUG SALARY_SLIP_EVENTS: ea_doc found: {'Yes' if ea_doc else 'No'}")
		salary_structure_doc = frappe.get_doc("Salary Structure", doc.salary_structure)

		# 2. Calculate Base, Allowances, and BPJS Base
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
			_custom_debug_log(f"DEBUG SALARY_SLIP_EVENTS: Allowances: {earnings_map}")

		bpjs_base = base_amount + tunjangan_tetap

		# BPJS Ditanggung Perusahaan (Earnings)
		earnings_map["JHT Perusahaan 3,7%"] = round(bpjs_base * 0.037)
		earnings_map["JKK 0,89%"] = round(bpjs_base * 0.0089)
		earnings_map["JKM 0,3%"] = round(bpjs_base * 0.003)
		earnings_map["JP Perusahaan 2%"] = round(bpjs_base * 0.02)
		earnings_map["JKN Perusahaan 4%"] = 0

		# Komponen sama di sisi potongan
		deductions_map.update(
			{
				"JHT Perusahaan 3,7%": earnings_map["JHT Perusahaan 3,7%"],
				"JKK 0,89%": earnings_map["JKK 0,89%"],
				"JKM 0,3%": earnings_map["JKM 0,3%"],
				"JP Perusahaan 2%": earnings_map["JP Perusahaan 2%"],
				"JKN Perusahaan 4%": earnings_map["JKN Perusahaan 4%"],
			}
		)

		# BPJS Ditanggung Karyawan (Deductions)
		deductions_map["JHT Karyawan 2%"] = round(bpjs_base * 0.02)
		deductions_map["JP Karyawan 1%"] = round(bpjs_base * 0.01)
		deductions_map["JKN Karyawan 1%"] = 0

		# 3. Calculate Overtime and LWP
		overtime_amount = calculate_overtime(doc)
		earnings_map["Overtime"] = overtime_amount

		absent_days = frappe.db.count(
			"Attendance",
			{
				"employee": doc.employee,
				"status": "Absent",
				"attendance_date": ["between", (doc.start_date, doc.end_date)],
			},
		)
		if absent_days > 0:
			working_days_in_month = 25
			daily_rate_for_deduction = bpjs_base / working_days_in_month
			deductions_map["Absensi"] = round(absent_days * daily_rate_for_deduction)
		else:
			deductions_map["Absensi"] = 0

		# 4. Fetch Additional Salary
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

		# 5. Calculate Gross Pay and PPh 21
		gross_pay_temp = sum(earnings_map.values())
		doc.gross_pay = gross_pay_temp  # Set gross_pay sementara untuk kalkulasi PPh
		_custom_debug_log(f"DEBUG SALARY_SLIP_EVENTS: Gross Pay before PPh21: {gross_pay_temp}")
		pph21_amount = calculate_pph21(doc)
		_custom_debug_log(f"DEBUG SALARY_SLIP_EVENTS: PPh21 Amount calculated: {pph21_amount}")
		deductions_map["Tax"] = pph21_amount

		# 6. Populate temporary lists from structure
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

		# 7. FINAL STEP: Jika semua kalkulasi berhasil, update dokumen
		doc.set("earnings", new_earnings)
		doc.set("deductions", new_deductions)

		# 8. Recalculate and set final totals
		doc.gross_pay = sum(e.get("amount") for e in new_earnings)
		doc.total_deduction = sum(d.get("amount") for d in new_deductions)
		doc.net_pay = doc.gross_pay - doc.total_deduction

		_custom_debug_log(
			f"DEBUG: Berhasil update semua {len(new_earnings)} earnings dan {len(new_deductions)} deductions. Net Pay: {doc.net_pay}"
		)

	except Exception as e:
		# Jika gagal, data lama dipertahankan, dan log error dicatat
		_custom_debug_log(f"ERROR: Kalkulasi gagal, data lama dipertahankan. Error: {e}")
		# Optional: re-raise the exception if you want the user to see a popup
		# frappe.throw(f"Calculation failed: {e}")
