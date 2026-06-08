import frappe
from frappe import _

from frappe.model.document import Document

class EmployeeAllowanceData(Document):
	def validate(self):
		validate_employee_allowance_data(self, "validate")

def validate_employee_allowance_data(doc, method):
	"""
	Validasi sebelum menyimpan Employee Allowance Data.
	Mencegah penyimpanan jika Shift (Assignment / Default Shift) belum diatur.
	"""
	if not doc.employee:
		return

	# Panggil fungsi utilitas yang sama dengan UI untuk mengecek status shift
	from hrd_siumang.payroll.payroll_utils import get_payroll_denominator_info
	info = get_payroll_denominator_info(doc.employee)
	
	if not info.get("has_shift"):
		frappe.throw(_("Karyawan <b>{0}</b> belum ditautkan ke Shift Type aktif. Harap atur <b>Shift Assignment</b> atau <b>Default Shift</b> pada Karyawan terlebih dahulu.").format(doc.employee), title=_("Shift Belum Diatur"))
