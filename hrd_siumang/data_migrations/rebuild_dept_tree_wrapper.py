import frappe
from frappe.utils import nestedset


def run():
	print("--- Attempting to rebuild Department tree via wrapper ---")
	try:
		nestedset.rebuild_tree("Department", "parent_department")
		frappe.db.commit()
		print("--- Department tree rebuild initiated successfully. ---")
	except Exception as e:
		print(f"❌ ERROR during Department tree rebuild: {e}")
		frappe.db.rollback()
