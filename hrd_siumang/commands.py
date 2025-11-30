import frappe
from frappe import _

# Import the actual task functions
from hrd_siumang.hrd_siumang.doctype.payroll_validation_process.payroll_validation_process import (
	process_absences_task,
	run_validation_task,
)

# Import the payroll dry-run test function
from hrd_siumang.payroll.scripts.test_payroll_flow_dry_run import (
	run_test as run_payroll_dry_run_test_script,
)


@frappe.whitelist()
def run_all_tests_from_bench(docname, job_user=None):
	"""
	Function to run validation and absence processing tasks directly from bench execute.
	This is for testing/debugging purposes.
	"""
	if not job_user:
		job_user = frappe.session.user if frappe.session.user != "Guest" else "Administrator"

	frappe.set_user(job_user)

	frappe.msgprint(
		_("--- Starting Payroll Validation Tests via bench execute ---"), title=_("Test Runner"), alert=True
	)
	frappe.msgprint(_("Fetching document: {0}").format(docname), title=_("Test Runner"), alert=True)

	try:
		# Step 1: Run Validation Task
		frappe.msgprint(_("Running Validation Task..."), title=_("Test Runner"), alert=True)
		run_validation_task(docname, job_user)
		frappe.msgprint(_("Validation Task Completed."), title=_("Test Runner"), alert=True)

		# Step 2: Run Absence Processing Task
		frappe.msgprint(_("Running Absence Processing Task..."), title=_("Test Runner"), alert=True)
		process_absences_task(docname, job_user)
		frappe.msgprint(_("Absence Processing Task Completed."), title=_("Test Runner"), alert=True)

		frappe.msgprint(
			_("--- All Payroll Validation Tests Completed Successfully ---"),
			title=_("Test Runner"),
			indicator="green",
			alert=True,
		)

	except Exception as e:
		frappe.msgprint(
			_("--- Payroll Validation Tests FAILED --- Error: {0}").format(str(e)),
			title=_("Test Runner"),
			indicator="red",
			alert=True,
		)
		frappe.log_error(frappe.get_traceback(), "Payroll Validation Bench Execute Test Failed")

	frappe.db.commit()  # Commit any changes made by the tasks


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
