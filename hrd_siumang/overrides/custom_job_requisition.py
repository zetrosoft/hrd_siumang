from frappe.model.document import Document


class CustomJobRequisition(Document):
	"""
	This class overrides the standard Job Requisition DocType controller.
	By mapping this class in hooks.py, we are telling the Frappe framework
	to use our custom app's definition (JSON, Python, etc.) for this DocType,
	effectively ignoring the standard one from ERPNext.

	This gives us full control over the DocType's fields, layout, and behavior,
	and prevents standard scripts from running, which should resolve the
	'Employee not found' error for the Administrator user.
	"""

	pass
