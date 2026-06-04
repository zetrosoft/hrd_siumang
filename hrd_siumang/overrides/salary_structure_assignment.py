import frappe


def set_base_from_ctc(doc, method):
	"""
	DocEvent for Salary Structure Assignment before_save.
	Automatically sets the 'base' amount of the SSA from the employee's CTC.
	Enforces validation to prevent 0 base, except for Harian/Borongan.
	"""
	if doc.employee:
		ctc = frappe.db.get_value("Employee", doc.employee, "ctc") or 0

		# If structure is Harian/Borongan, allow CTC 0 because salary is performance-based
		if doc.salary_structure == "Struktur Gaji - Harian":
			doc.base = ctc
			return

		# Strict Validation for regular structures
		if ctc <= 0:
			frappe.throw(
				f"Gagal Assign: Karyawan <b>{doc.employee}</b> tidak memiliki nilai CTC (Cost to Company).<br>"
				f"Silakan isi CTC di Master Employee terlebih dahulu sebelum melakukan assign skema gaji reguler."
			)
		else:
			doc.base = ctc
			frappe.msgprint(f"Base amount set from Employee's CTC: {frappe.format(ctc, 'Currency')}")
