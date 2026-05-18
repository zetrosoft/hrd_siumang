from datetime import date

import frappe
from frappe import _

# Import the functions to be tested
from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21


def run_test():
	"""
	Runs a specific test scenario for calculate_overtime and calculate_pph21
	using user-provided mock data.
	"""
	print("\n--- Menjalankan Tes Skenario Spesifik ---")

	# User-provided parameters
	employee_id = "HR-EMP-00003"

	start_date_test = date(2025, 8, 1)
	end_date_test = date(2025, 8, 31)

	# User-provided earnings data
	mock_earnings_data = [
		frappe._dict({"salary_component": "Gaji Pokok", "amount": 10500000}),
		frappe._dict({"salary_component": "Tunjangan Jabatan", "amount": 2500000}),
		frappe._dict({"salary_component": "Tunjangan Komunikasi", "amount": 500000}),
		frappe._dict({"salary_component": "Tunjangan Transport", "amount": 3000000}),
		frappe._dict({"salary_component": "Tunjangan Makan", "amount": 1780000}),
	]

	# Pre-calculated common deductions for PPh 21 logic
	common_deductions = [
		frappe._dict({"salary_component": "JHT Karyawan", "amount": 100000}),
		frappe._dict({"salary_component": "JP Karyawan", "amount": 50000}),
	]

	# Calculate gross_pay from mock_earnings_data
	calculated_gross_pay = sum(item.amount for item in mock_earnings_data)

	# Create a mock Salary Slip document
	mock_slip = frappe._dict(
		{
			"employee": employee_id,
			"employee_name": frappe.get_value("Employee", employee_id, "employee_name")
			or "Test Employee Name",
			"start_date": start_date_test,
			"end_date": end_date_test,
			"base": 10500000,  # Gaji Pokok (needed for upah_per_jam)
			"gross_pay": calculated_gross_pay,
			"earnings": [
				*mock_earnings_data,  # Add mock JKK/JKM for PPh 21 calculation
				frappe._dict({"salary_component": "JKK Perusahaan", "amount": 44500}),
				frappe._dict({"salary_component": "JKM Perusahaan", "amount": 15000}),
			],
			"deductions": common_deductions,
		}
	)

	print(f"Menguji skenario untuk Karyawan: {mock_slip.employee_name} ({employee_id})")
	print(f"Periode: {start_date_test} s/d {end_date_test}")
	print(f"Gross Pay Dasar (dari pendapatan mock): Rp {calculated_gross_pay:,.2f}")
	print(f"Gaji Pokok (Base): Rp {mock_slip.base:,.2f}")

	# --- Test calculate_overtime ---
	print("\n--- Hasil Kalkulasi Overtime ---")
	calculated_overtime_amount = calculate_overtime(mock_slip)
	print(f"Jumlah Lembur Terhitung: Rp {calculated_overtime_amount:,.2f}")

	# --- Test calculate_pph21 ---
	print("\n--- Hasil Kalkulasi PPh 21 ---")
	calculated_pph21_amount = 0
	try:
		calculated_pph21_amount = calculate_pph21(mock_slip)
		print(f"Jumlah PPh 21 Terhitung: Rp {calculated_pph21_amount:,.2f}")
	except Exception as e:
		print(f"❌ Error saat kalkulasi PPh 21: {e}")
		frappe.log_error(frappe.get_traceback(), "Tes Skenario Spesifik - Kalkulasi PPh 21 Gagal")
		print("Detail Error tercatat di Frappe Error Log.")
		calculated_pph21_amount = 0  # Ensure it's 0 if error occurs

	# --- Final Summary ---
	print("\n--- Ringkasan Slip Gaji (Mock) ---")
	total_earnings_display = calculated_gross_pay + calculated_overtime_amount
	total_deductions_display = calculated_pph21_amount + sum(item.amount for item in common_deductions)
	net_pay_display = total_earnings_display - total_deductions_display

	print(f"Total Pendapatan (Termasuk Lembur): Rp {total_earnings_display:,.2f}")
	print(f"Total Potongan (Termasuk PPh 21): Rp {total_deductions_display:,.2f}")
	print(f"Net Pay (Perkiraan): Rp {net_pay_display:,.2f}")
	print("-------------------------------------------\n")

	# Important: No frappe.db.commit() means no permanent changes.
	# bench execute automatically rolls back if no commit is made.
