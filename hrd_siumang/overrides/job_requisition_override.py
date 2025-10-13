import frappe


def before_save(doc, method):
	"""
	Populates a simple text field 'pendidikan_list' from the 'pendidikan' table
	for better list view display.
	"""
	# Assuming 'pendidikan' is a Table (Child Table) field in Job Requisition
	# and the child doctype has a field named 'education_level' which we want to display.
	# This is a common pattern. If the field name is different, it needs to be adjusted.

	if hasattr(doc, "pendidikan") and doc.pendidikan:
		try:
			# Collect the 'education_level' from each row in the 'pendidikan' table
			pendidikan_entries = [
				d.get("education_level") for d in doc.pendidikan if d.get("education_level")
			]

			# Join them into a single comma-separated string
			doc.pendidikan_list = ", ".join(pendidikan_entries)
		except Exception as e:
			# If the structure is not as expected, log the error and set a default value
			frappe.log_error(
				f"Error formatting 'pendidikan' for list view: {e}", "Job Requisition Custom Logic"
			)
			doc.pendidikan_list = "Error reading education details"
	elif hasattr(doc, "pendidikan") and not doc.pendidikan:
		doc.pendidikan_list = ""
