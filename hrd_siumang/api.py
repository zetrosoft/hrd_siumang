import frappe
from frappe import _


@frappe.whitelist()
def get_department_approver(department_name: str) -> str | None:
	"""
	Fetches the approver for a given department.
	Assumes Department DocType has a child table custom field that links to 'Department Approver' DocType.
	"""
	if not department_name:
		return None

	custom_table_field = frappe.get_all(
		"Custom Field",
		filters={
			"dt": "Department",
			"fieldtype": "Table",
			"options": "Department Approver",
		},
		fields=["fieldname"],
		limit=1,
	)

	if not custom_table_field:
		frappe.log_error(
			"No custom table field found on Department linking to 'Department Approver'.",
			"Department Approver Lookup",
		)
		return None

	approver = frappe.get_all(
		"Department Approver",
		filters={
			"parenttype": "Department",
			"parent": department_name,
		},
		fields=["approver"],
		limit=1,
	)

	if approver:
		return approver[0].approver
	else:
		frappe.log_error(
			f"No approver found in Department Approver child table for department: {department_name}",
			"Department Approver Lookup",
		)
		return None
