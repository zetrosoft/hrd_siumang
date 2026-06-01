import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from sales_monitor.override_payroll import patched_calculate_net_pay


class CustomSalarySlip(SalarySlip):
	"""
	This custom class overrides the standard SalarySlip controller.
	Its purpose is to surgically disable specific methods from the core HRMS app
	that conflict with the custom calculation logic in hrd_siumang.
	"""

	def calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
		"""
		This is the primary override point.
		It checks if the Salary Slip is for an incentive and routes accordingly.
		"""
		# Check if this Payroll Entry is linked to an Employee Incentive.
		# This is the definitive check to identify an incentive-based payroll run.
		is_incentive_slip = False
		if self.payroll_entry:
			is_incentive_pe = frappe.db.get_value(
				"Payroll Entry", self.payroll_entry, "custom_incentive_employee_incentive"
			)
			if is_incentive_pe:
				is_incentive_slip = True

		if is_incentive_slip:
			# If it's an incentive slip, we call the specific logic defined in our
			# sales_monitor patch. This function is designed to handle only incentives.
			return patched_calculate_net_pay(self, skip_tax_breakup_computation)
		else:
			# If it's a normal payroll run, we call our custom calculator directly here.
			# This ensures that when the user clicks 'Get Employee Details' on the UI,
			# the structure and totals are built and displayed immediately.
			from hrd_siumang.payroll.salary_slip_events import calculate_payroll_components
			
			calculate_payroll_components(self, None)
			
			# After setting the custom components, we need to ensure the standard 
			# totals are calculated based on the new earnings and deductions.
			self.set_totals()

	def add_tax_components(self):
		"""
		This method is intentionally overridden to do nothing.
		The core `add_tax_components` function automatically adds tax components
		if it believes none exist, which conflicts with our custom tax calculation.
		Neutralizing this prevents unwanted components from being added and
		interfering with our calculations.
		"""
		# We add a log to confirm this patch is working.
		pass


	# By NOT overriding the main 'validate' method, we allow the original
	# `validate` to run. It will perform its setup functions (like get_working_days_details),
	# but when it attempts to call the two methods defined above (`calculate_net_pay`
	# and `add_tax_components`), it will execute our empty versions instead of the
	# original, destructive ones.
