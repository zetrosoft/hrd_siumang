import frappe
from frappe.utils import getdate


def run_debug(payroll_entry_name):
	"""
	Debugs why employees are not being fetched for a specific Payroll Entry.
	To run: bench --site [your.site] execute frappe-bench/apps/hrd_siumang/hrd_siumang/debug_payroll_employees.py run_debug --args '["PAY-00001"]'
	"""
	if not frappe.db.exists("Payroll Entry", payroll_entry_name):
		print(f"ERROR: Payroll Entry '{payroll_entry_name}' not found.")
		return

	try:
		pe = frappe.get_doc("Payroll Entry", payroll_entry_name)
		print(f"--- Debugging Payroll Entry: {payroll_entry_name} ---")

		# 1. Get Filters from Payroll Entry
		print("\n[1] Filters constructed from Payroll Entry:")
		filters = pe.make_filters()
		for key, value in filters.items():
			print(f"  - {key}: {value}")

		# 2. Check for matching Salary Structures
		print("\n[2] Finding matching Salary Structures...")
		from hrms.payroll.doctype.payroll_entry.payroll_entry import get_salary_structure

		sal_structs = get_salary_structure(
			filters.company,
			filters.currency,
			filters.salary_slip_based_on_timesheet,
			filters.payroll_frequency,
		)

		if not sal_structs:
			print("  !!! FAILURE: No active Salary Structures found for the criteria above.")
			print("      Please check Company, Currency, and Payroll Frequency on your Salary Structures.")
			return
		else:
			print(f"  SUCCESS: Found {len(sal_structs)} matching Salary Structure(s):")
			for s in sal_structs:
				print(f"    - {s}")

		# 3. Check for Employees based on all filters
		print("\n[3] Fetching final employee list (with all filters)...")
		from hrms.payroll.doctype.payroll_entry.payroll_entry import get_filtered_employees

		emp_list = get_filtered_employees(sal_structs, filters, as_dict=True)

		if not emp_list:
			print("  !!! FAILURE: Final employee list is empty.")
			print("\n--- Running deeper analysis... ---")

			# Analysis A: Check employees matching basic criteria
			print(
				"\n[A] Checking for employees matching basic criteria (Status, Company, Dates, Optional Filters)..."
			)
			Employee = frappe.qb.DocType("Employee")
			basic_emp_query = (
				frappe.qb.from_(Employee)
				.select(
					Employee.name,
					Employee.status,
					Employee.date_of_joining,
					Employee.relieving_date,
					Employee.company,
				)
				.where(
					(Employee.status != "Inactive")
					& (Employee.company == filters.company)
					& ((Employee.date_of_joining <= filters.end_date) | (Employee.date_of_joining.isnull()))
					& ((Employee.relieving_date >= filters.start_date) | (Employee.relieving_date.isnull()))
				)
			)
			# Add optional filters from Payroll Entry
			for fltr_key in ["branch", "department", "designation", "grade"]:
				if filters.get(fltr_key):
					basic_emp_query = basic_emp_query.where(Employee[fltr_key] == filters[fltr_key])

			basic_employees = basic_emp_query.run(as_dict=True)

			if not basic_employees:
				print(
					"  - RESULT: No employees found that match the basic criteria (Company, Department, Dates, etc.)."
				)
				print("    -> Please check the filters in Step [1] against your employee records.")
			else:
				print(f"  - RESULT: Found {len(basic_employees)} employee(s) matching basic criteria.")
				print("    -> This suggests the problem is with the 'Salary Structure Assignment'.")

				# Analysis B: Check SSA for these employees
				print(
					"\n[B] Analyzing 'Salary Structure Assignment' for these {len(basic_employees)} employees..."
				)
				ssa_employees = frappe.get_all(
					"Salary Structure Assignment",
					filters={"employee": ["in", [e.name for e in basic_employees]]},
					fields=[
						"employee",
						"docstatus",
						"from_date",
						"salary_structure",
						"payroll_payable_account",
					],
				)

				if not ssa_employees:
					print("  - RESULT: None of these employees have any Salary Structure Assignment at all.")
				else:
					print(f"  - RESULT: Found {len(ssa_employees)} assignment(s). Details:")
					all_match = True
					for ssa in ssa_employees:
						status_ok = ssa.docstatus == 1
						date_ok = getdate(ssa.from_date) <= getdate(filters.end_date)
						struct_ok = ssa.salary_structure in sal_structs
						payable_acc_ok = ssa.payroll_payable_account == filters.payroll_payable_account

						if not (status_ok and date_ok and struct_ok and payable_acc_ok):
							all_match = False

						print(f"    - Employee: {ssa.employee}")
						print(f"      - Status Submitted? {'OK' if status_ok else 'FAIL (is Draft)'}")
						print(
							f"      - From Date <= End Date? {'OK' if date_ok else f'FAIL ({ssa.from_date} > {filters.end_date})'}"
						)
						print(
							f"      - Structure in list? {'OK' if struct_ok else f'FAIL ({ssa.salary_structure} not in {sal_structs})'}"
						)
						print(
							f"      - Payable Account Match? {'OK' if payable_acc_ok else f'FAIL ({ssa.payroll_payable_account} != {filters.payroll_payable_account})'}"
						)

					if all_match:
						print(
							"\n  - CONCLUSION: All assignments seem correct. There might be another subtle issue. Please double-check for typos or hidden filters."
						)
					else:
						print(
							"\n  - CONCLUSION: One or more Salary Structure Assignments have failing conditions. Please correct them based on the details above."
						)

		else:
			print(f"  SUCCESS: Found {len(emp_list)} employee(s):")
			for e in emp_list:
				print(f"    - {e.employee} ({e.employee_name})")

	except Exception as e:
		print("\n--- AN ERROR OCCURRED ---")
		frappe.log_error("Payroll Debug Script Error")
		print(frappe.get_traceback())
