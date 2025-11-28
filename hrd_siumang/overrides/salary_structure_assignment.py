import frappe


def set_base_from_ctc(doc, method):
	"""
	DocEvent for Salary Structure Assignment before_save.
	Automatically sets the 'base' amount of the SSA from the employee's CTC.
	"""
	if doc.employee:
		ctc = frappe.db.get_value("Employee", doc.employee, "ctc")
		if ctc is not None and ctc >= 0:  # Ensure ctc is a valid number
			doc.base = ctc
			frappe.msgprint(f"Base amount set from Employee's CTC: {frappe.format(ctc, 'Currency')}")
		else:
			frappe.msgprint(
				f"Peringatan: CTC tidak ditemukan atau tidak valid untuk karyawan {doc.employee}. Base amount tidak diisi otomatis."
			)
