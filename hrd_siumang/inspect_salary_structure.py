import frappe


def inspect_doctype_fields():
	"""
	Inspects and prints all fields of the Salary Component doctype.
	"""
	try:
		frappe.set_user("Administrator")
		salary_component_doctype = frappe.get_doc("DocType", "Salary Component")

		print("\n--- Inspeksi Doctype Salary Component Fields ---")
		print(f"Doctype: {salary_component_doctype.name}")
		print("--- Fields ---")
		for field in salary_component_doctype.fields:
			print(
				f"  - Fieldname: {field.fieldname}, Label: {field.label}, Fieldtype: {field.fieldtype}, Options: {field.options}"
			)
		print("-----------------------------------------\n")

	except Exception as e:
		print(f"❌ GAGAL saat menginspeksi Doctype fields: {e}")


def run():
	"""Wrapper function to be called by bench execute."""
	inspect_doctype_fields()
