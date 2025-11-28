from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

from hrd_siumang.payroll.payroll_utils import calculate_overtime


class CustomSalarySlip(SalarySlip):
	def get_overtime_amount(self):
		"""
		Custom method to call the calculate_overtime function.
		This allows the formula in Salary Component to call `doc.get_overtime_amount()`.
		"""
		# The calculate_overtime function expects the Salary Slip document itself.
		# 'self' refers to the current Salary Slip document.
		return calculate_overtime(self)

	# You can override other methods of SalarySlip here if needed
	# For example, to modify its default behavior.
