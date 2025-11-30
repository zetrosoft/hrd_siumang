from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

# Import the core payroll calculation functions
from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21
from hrd_siumang.payroll.salary_slip_events import calculate_payroll_components


def setup_dummy_data(
	employee_id="HR-EMP-00003", company="PT. SIUMANG TEMAN SUKSES"
):  # <--- Diperbaiki: employee_id default
	"""
	Sets up minimal dummy data for testing.
	This function will create Employee, Salary Structure Assignment,
	and Employee Allowance Data if they don't exist.
	"""
	frappe.set_user("Administrator")
	print("\n--- Setup Dummy Data ---")

	# 1. Create Dummy Employee if not exists
	if not frappe.db.exists("Employee", employee_id):
		try:
			employee = frappe.new_doc("Employee")
			employee.employee = employee_id
			employee.employee_name = "Test Employee One"
			employee.company = company
			employee.status = "Active"
			employee.date_of_joining = "2024-01-01"
			employee.ctc = 10000000.00  # Base for calculations
			employee.status_pajak = "TK/0"  # For PPh21 calculation
			employee.gender = "Male"
			# Try to get any existing Holiday List, or create a simple one if none exists
			existing_holiday_list = frappe.get_all("Holiday List", filters={}, limit=1, pluck="name")
			employee.holiday_list = existing_holiday_list[0] if existing_holiday_list else None

			if not employee.holiday_list:
				print("WARNING: No Holiday List found. Creating a dummy one.")
				hl = frappe.new_doc("Holiday List")
				hl.holiday_list_name = "Standard Holiday List"
				hl.from_date = "2024-01-01"
				hl.to_date = "2025-12-31"
				hl.append("holidays", {"date": "2025-01-01", "description": "New Year"})
				hl.save(ignore_permissions=True)
				employee.holiday_list = "Standard Holiday List"
				frappe.db.commit()  # Commit new Holiday List to make it available for the employee

			employee.save(ignore_permissions=True)
			# frappe.db.commit() # Removed commit for dry-run
			# frappe.reload_doctype('Employee') # Removed, as it causes environment issues
			print(f"✅ Dummy Employee {employee_id} created.")
		except Exception as e:
			print(f"❌ Failed to create Dummy Employee: {e}")
			frappe.log_error(frappe.get_traceback(), "Test Script Dummy Employee Creation Failed")
			return None
	else:
		print(f"Info: Dummy Employee {employee_id} already exists. Updating...")
		employee = frappe.get_doc("Employee", employee_id, ignore_permissions=True)
		employee.ctc = 10000000.00
		employee.status_pajak = "TK/0"
		# Try to get any existing Holiday List, or create a simple one if none exists
		existing_holiday_list = frappe.get_all("Holiday List", filters={}, limit=1, pluck="name")
		employee.holiday_list = existing_holiday_list[0] if existing_holiday_list else None

		if not employee.holiday_list:
			print("WARNING: No Holiday List found. Creating a dummy one.")
			hl = frappe.new_doc("Holiday List")
			hl.holiday_list_name = "Standard Holiday List"
			hl.from_date = "2024-01-01"
			hl.to_date = "2025-12-31"
			hl.append("holidays", {"date": "2025-01-01", "description": "New Year"})
			hl.save(ignore_permissions=True)
			employee.holiday_list = "Standard Holiday List"
			frappe.db.commit()  # Commit new Holiday List to make it available for the employee

		employee.save(ignore_permissions=True)
		# frappe.db.commit() # Removed commit for dry-run
		# frappe.reload_doctype('Employee') # Removed, as it causes environment issues

	# 2. Create Dummy Salary Structure Assignment if not exists
	structure_name = "Struktur Gaji - Test"
	if not frappe.db.exists("Salary Structure", structure_name):
		# Create a minimal dummy Salary Structure
		ss = frappe.new_doc("Salary Structure")
		ss.salary_structure_name = structure_name
		ss.company = company
		ss.is_active = "Yes"
		ss.payroll_payable_account = (
			"2131.001 - Biaya Yang Akan di Bayar - SIUMANG"  # Assuming this account exists
		)
		ss.currency = frappe.get_cached_value("Company", company, "default_currency")
		ss.append("earnings", {"salary_component": "Gaji Pokok"})
		ss.append("deductions", {"salary_component": "Tax PPh21"})  # Include PPh21
		ss.save(ignore_permissions=True)
		ss.submit()
		frappe.db.commit()  # Commit new Salary Structure
		print(f"✅ Dummy Salary Structure '{structure_name}' created.")
	else:
		print(f"Info: Dummy Salary Structure '{structure_name}' already exists.")

	if not frappe.db.exists("Salary Structure Assignment", {"employee": employee_id, "docstatus": 1}):
		try:
			ssa = frappe.new_doc("Salary Structure Assignment")
			ssa.employee = employee_id
			ssa.salary_structure = structure_name
			ssa.from_date = "2024-01-01"
			ssa.base = employee.ctc
			ssa.save(ignore_permissions=True)
			ssa.submit()
			# frappe.db.commit() # Removed commit for dry-run
			# frappe.reload_doc('hrms', 'payroll', 'salary_structure_assignment') # Removed, as it causes environment issues
			print(f"✅ Dummy Salary Structure Assignment for {employee_id} created.")
		except Exception as e:
			print(f"❌ Failed to create Dummy SSA: {e}")
			frappe.log_error(frappe.get_traceback(), "Test Script Dummy SSA Creation Failed")
	else:
		print(f"Info: Dummy Salary Structure Assignment for {employee_id} already exists.")
		# Update existing SSA if needed
		existing_ssa = frappe.get_all(
			"Salary Structure Assignment", filters={"employee": employee_id, "docstatus": 1}, limit=1
		)
		if existing_ssa:
			ssa_doc = frappe.get_doc("Salary Structure Assignment", existing_ssa[0].name)
			if ssa_doc.salary_structure != structure_name or ssa_doc.base != employee.ctc:
				ssa_doc.salary_structure = structure_name
				ssa_doc.base = employee.ctc
				ssa_doc.save(ignore_permissions=True)
				# frappe.db.commit() # Removed commit for dry-run
				# frappe.reload_doc('hrms', 'payroll', 'salary_structure_assignment') # Removed, as it causes environment issues
				print(f"Info: Existing SSA for {employee_id} updated.")

	# 3. Create Dummy Employee Allowance Data if not exists
	if not frappe.db.exists("Employee Allowance Data", {"employee": employee_id}):
		try:
			ea_data = frappe.new_doc("Employee Allowance Data")
			ea_data.employee = employee_id
			ea_data.tunjangan_jabatan = 1500000
			ea_data.tunjangan_komunikasi = 250000
			ea_data.tunjangan_transport = 500000
			ea_data.tunjangan_makan = 300000
			ea_data.tunjangan_lain = 100000
			ea_data.save(ignore_permissions=True)
			frappe.db.commit()  # Commit this specifically for the test to pick it up reliably
			print(f"✅ Dummy Employee Allowance Data for {employee_id} created.")
		except Exception as e:
			print(f"❌ Failed to create Dummy Employee Allowance Data: {e}")
			frappe.log_error(frappe.get_traceback(), "Test Script Dummy EA Data Creation Failed")
	else:
		print(
			f"Info: Dummy Employee Allowance Data for {employee_id} already exists. Updating..."
		)  # <--- Diperbaiki
		ea_data = frappe.get_doc("Employee Allowance Data", {"employee": employee_id})
		ea_data.tunjangan_jabatan = 1500000
		ea_data.tunjangan_komunikasi = 250000
		ea_data.tunjangan_transport = 500000
		ea_data.tunjangan_makan = 300000
		ea_data.tunjangan_lain = 100000
		ea_data.save(ignore_permissions=True)
		frappe.db.commit()

	# 4. Create Dummy Overtime Planning (optional, for overtime calculation test)
	# This is optional and can be complex, for a basic dry run, we'll assume no overtime for now.
	# If a full overtime test is needed, this part would be elaborated.
	print("--- Dummy Data Setup Complete ---")


def run_test():
	"""
	Runs a dry-run test of the payroll flow for a dummy employee.
	This function creates a mock Salary Slip and calls the calculation logic.
	"""
	frappe.set_user("Administrator")
	print("\n--- Starting Payroll Flow Dry-Run Test ---")

	employee_id = "HR-EMP-00003"  # <--- Diperbaiki
	company = "PT. SIUMANG TEMAN SUKSES"
	payroll_period_start = date(2025, 10, 1)
	payroll_period_end = date(2025, 10, 31)

	setup_dummy_data(employee_id, company)

	try:
		# Create a mock Salary Slip document
		mock_salary_slip = frappe.new_doc("Salary Slip")
		mock_salary_slip.employee = employee_id
		mock_salary_slip.employee_name = frappe.db.get_value("Employee", employee_id, "employee_name")
		mock_salary_slip.company = company
		mock_salary_slip.start_date = payroll_period_start
		mock_salary_slip.end_date = payroll_period_end

		# Get actual salary structure from SSA
		ssa = frappe.get_doc("Salary Structure Assignment", {"employee": employee_id, "docstatus": 1})
		mock_salary_slip.salary_structure = ssa.salary_structure

		# Simulate the before_save hook call
		print(f"\nSimulating calculate_payroll_components for {mock_salary_slip.employee_name}...")
		calculate_payroll_components(mock_salary_slip, "before_save")

		print("\n--- Resulting Mock Salary Slip ---")
		print(f"Employee: {mock_salary_slip.employee_name} ({mock_salary_slip.employee})")
		print(f"Period: {mock_salary_slip.start_date} to {mock_salary_slip.end_date}")
		print(f"Base Salary: {frappe.format(mock_salary_slip.base, 'Currency')}")

		print("\nEarnings:")
		for earning in mock_salary_slip.earnings:
			print(f"  - {earning.salary_component}: {frappe.format(earning.amount, 'Currency')}")
		print(f"Gross Pay: {frappe.format(mock_salary_slip.gross_pay, 'Currency')}")

		print("\nDeductions:")
		for deduction in mock_salary_slip.deductions:
			print(f"  - {deduction.salary_component}: {frappe.format(deduction.amount, 'Currency')}")
		print(f"Total Deduction: {frappe.format(mock_salary_slip.total_deduction, 'Currency')}")

		print(f"\nNet Pay: {frappe.format(mock_salary_slip.net_pay, 'Currency')}")

		print("\n--- Payroll Flow Dry-Run Test Complete ---")

	except Exception as e:
		print(f"❌ Payroll Flow Dry-Run Test FAILED: {e}")
		frappe.log_error(frappe.get_traceback(), "Payroll Flow Dry-Run Test Failed")
		frappe.msgprint(_("Payroll Flow Dry-Run Test FAILED. Check error log for details."), indicator="red")
	finally:
		# Frappe's bench execute automatically rolls back changes if no frappe.db.commit() is called
		# For setup_dummy_data, we explicitly committed, so need to clean up if we want full isolation
		# For simplicity in this dry run, we'll let bench rollback the mock_salary_slip
		# and assume manual cleanup of dummy master data if needed after multiple runs.
		print("\nNote: Changes to mock Salary Slip are temporary (dry-run). Dummy master data might persist.")
		frappe.db.rollback()  # Ensure everything is rolled back if setup_dummy_data committed something unexpectedly
