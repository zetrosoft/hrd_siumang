import frappe
from frappe import _


def create_status_pajak_field():
	"""
	Creates a custom field 'status_pajak' of type Select on the Employee DocType.
	"""
	frappe.set_user("Administrator")  # Ensure we have necessary permissions

	doctype_name = "Employee"
	fieldname = "status_pajak"
	label = "Status Pajak"
	fieldtype = "Select"
	options = "TK/0\nK/0\nK/1\nK/2\nK/3"  # Common PTKP statuses

	# Check if the custom field already exists
	if frappe.db.exists("Custom Field", {"dt": doctype_name, "fieldname": fieldname}):
		print(f"✅ Custom Field '{label}' ({fieldname}) sudah ada di DocType '{doctype_name}'.")
		return

	try:
		cf = frappe.new_doc("Custom Field")
		cf.dt = doctype_name
		cf.fieldname = fieldname
		cf.label = label
		cf.fieldtype = fieldtype
		cf.options = options
		cf.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"✅ Berhasil membuat Custom Field '{label}' ({fieldname}) di DocType '{doctype_name}'.")
	except Exception as e:
		frappe.db.rollback()
		print(f"❌ Gagal membuat Custom Field '{label}' ({fieldname}): {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Membuat Custom Field Status Pajak")


# This is the entry point for bench execute
