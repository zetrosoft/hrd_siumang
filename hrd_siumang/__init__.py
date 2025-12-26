import frappe

from .patches import monkey_patch_payroll

# This code runs once when the app is loaded by a python process.
# We are calling our patch function from here to ensure it runs reliably.
monkey_patch_payroll.apply_patch()

# Create a visible log entry to confirm that this patch execution was attempted.
# This can be viewed from the "Error Log" list in the Frappe UI.
frappe.log_error(
	message="HRD Siumang startup patch process has been executed.", title="HRD Siumang Patch Initializer"
)
