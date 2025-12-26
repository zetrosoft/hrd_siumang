import frappe


def apply_patch():
	"""
	This patch disables conflicting Salary Slip hooks from 'payroll_indonesia' and core 'hrms'
	by replacing them with functions that do nothing. This ensures that 'hrd_siumang'
	has full control over the salary slip calculation process.
	"""
	# --- Patch for 'payroll_indonesia' app ---
	try:
		from payroll_indonesia.override import salary_slip_functions

		def do_nothing_pi(*args, **kwargs):
			# Using a unique name to avoid scope issues if debugging
			frappe.logger("monkey_patch").info(
				f"Skipping execution of patched payroll_indonesia function for doc: {args[0].name if args else 'N/A'}"
			)
			pass

		if hasattr(salary_slip_functions, "validate_salary_slip"):
			salary_slip_functions.validate_salary_slip = do_nothing_pi
			frappe.logger("monkey_patch").info(
				"Successfully patched payroll_indonesia.override.salary_slip_functions.validate_salary_slip"
			)

		if hasattr(salary_slip_functions, "on_submit_salary_slip"):
			salary_slip_functions.on_submit_salary_slip = do_nothing_pi
			frappe.logger("monkey_patch").info(
				"Successfully patched payroll_indonesia.override.salary_slip_functions.on_submit_salary_slip"
			)

	except (ImportError, AttributeError):
		# This is expected if 'payroll_indonesia' is uninstalled.
		frappe.logger("monkey_patch").info("'payroll_indonesia' app not found, skipping patch.")
		pass

	# --- Patch for core 'hrms' app ---
	try:
		from hrms.payroll.doctype.salary_slip import salary_slip

		def do_nothing_hrms(*args, **kwargs):
			doc_name = "N/A"
			if args and hasattr(args[0], "name"):
				doc_name = args[0].name
			frappe.logger("monkey_patch").info(
				f"Skipping execution of patched HRMS salary_slip function for doc: {doc_name}"
			)
			pass

		# Disable the tax component auto-addition
		if hasattr(salary_slip.SalarySlip, "add_tax_components"):
			salary_slip.SalarySlip.add_tax_components = do_nothing_hrms
			frappe.logger("monkey_patch").info(
				"Successfully patched hrms.payroll.doctype.salary_slip.salary_slip.SalarySlip.add_tax_components"
			)

		# Disable the entire recalculation orchestrator
		if hasattr(salary_slip.SalarySlip, "calculate_net_pay"):
			salary_slip.SalarySlip.calculate_net_pay = do_nothing_hrms
			frappe.logger("monkey_patch").info(
				"Successfully patched hrms.payroll.doctype.salary_slip.salary_slip.SalarySlip.calculate_net_pay"
			)

	except (ImportError, AttributeError) as e:
		frappe.logger("monkey_patch").warning(f"Failed to apply patch to core HRMS salary slip: {e}")
