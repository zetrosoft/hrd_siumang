import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class CustomSalarySlip(SalarySlip):
	"""
	This custom class overrides the standard SalarySlip controller.
	Its purpose is to surgically disable specific methods from the core HRMS app
	that conflict with the custom calculation logic in hrd_siumang.
	"""

	def calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
		"""
		This method is intentionally overridden to do nothing.
		The core `calculate_net_pay` function orchestrates a full recalculation
		of all components, which overwrites the values correctly calculated
		by our custom `before_save` hook. By neutralizing this method,
		we allow our custom app to be the sole source of truth for calculations.
		"""
		# We add a log to confirm this patch is working.
		# This can be viewed from the "Error Log" list in the Frappe UI.
		frappe.log_error(
			title="HRD Siumang Override",
			message=f"Skipping core `calculate_net_pay` for {self.name} via class override.",
		)
		pass

	def add_tax_components(self):
		"""
		This method is intentionally overridden to do nothing.
		The core `add_tax_components` function automatically adds tax components
		if it believes none exist, which conflicts with our custom tax calculation.
		Neutralizing this prevents unwanted components from being added and
		interfering with our calculations.
		"""
		# We add a log to confirm this patch is working.
		frappe.log_error(
			title="HRD Siumang Override",
			message=f"Skipping core `add_tax_components` for {self.name} via class override.",
		)
		pass

	# By NOT overriding the main 'validate' method, we allow the original
	# `validate` to run. It will perform its setup functions (like get_working_days_details),
	# but when it attempts to call the two methods defined above (`calculate_net_pay`
	# and `add_tax_components`), it will execute our empty versions instead of the
	# original, destructive ones.
