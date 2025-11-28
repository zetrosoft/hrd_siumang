from datetime import date

import frappe
from frappe._dict import _dict


def test_overtime_whitelist_call():
	"""
	Tests if calculate_overtime can be called via frappe.call,
	which relies on whitelisted methods.
	"""
	print("\n--- Testing Whitelisted calculate_overtime Call ---")
	employee_id = "HR-EMP-00003"

	# Create a mock Salary Slip object for the function call
	mock_slip = _dict(
		{
			"employee": employee_id,
			"employee_name": frappe.get_value("Employee", employee_id, "employee_name")
			or "Test Employee Name",
			"start_date": date(2025, 8, 1),
			"end_date": date(2025, 8, 31),
			"base": 10500000,
			"gross_pay": 18280000,
			"earnings": [],  # Not needed for this specific test
			"deductions": [],  # Not needed for this specific test
		}
	)

	try:
		# Call the whitelisted method directly
		result = frappe.call("hrd_siumang.payroll.payroll_utils.calculate_overtime", doc=mock_slip)
		print(f"✅ Panggilan frappe.call untuk calculate_overtime berhasil. Hasil: {result}")
	except Exception as e:
		print(f"❌ Panggilan frappe.call untuk calculate_overtime GAGAL. Error: {e}")
		frappe.log_error(frappe.get_traceback(), "Tes Whitelist Call Gagal")

	print("----------------------------------------------------\n")


# This is the entry point for bench execute
