import frappe
from frappe import _

# Import the payroll dry-run test function
from hrd_siumang.payroll.scripts.test_payroll_flow_dry_run import (
	run_test as run_payroll_dry_run_test_script,
)


@frappe.whitelist()
def run_payroll_dry_run_test():
	"""
	Runs the payroll flow dry-run test script.
	Usage: bench execute hrd_siumang.hrd_siumang.commands.run_payroll_dry_run_test
	"""
	frappe.set_user("Administrator")
	frappe.msgprint(
		_("--- Starting Payroll Flow Dry-Run Test via bench execute ---"),
		title=_("Payroll Dry-Run Test"),
		alert=True,
	)
	try:
		run_payroll_dry_run_test_script()
		frappe.msgprint(
			_("--- Payroll Flow Dry-Run Test Completed ---"),
			title=_("Payroll Dry-Run Test"),
			indicator="green",
			alert=True,
		)
	except Exception as e:
		frappe.msgprint(
			_("--- Payroll Flow Dry-Run Test FAILED --- Error: {0}").format(str(e)),
			title=_("Payroll Dry-Run Test"),
			indicator="red",
			alert=True,
		)
		frappe.log_error(frappe.get_traceback(), "Payroll Dry-Run Test Bench Execute Failed")
	finally:
		frappe.db.rollback()  # Ensure no changes are committed from the test
