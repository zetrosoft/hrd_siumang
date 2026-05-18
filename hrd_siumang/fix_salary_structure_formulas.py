# Copyright (c) 2025, PT. SIUMANG TEMAN SUKSES and contributors
# For license information, please see license.txt

import frappe

# List of components whose formulas should be disabled
COMPONENTS_TO_FIX = [
	"JHT Perusahaan",
	"JKK Perusahaan",
	"JKM Perusahaan",
	"JP Perusahaan",
	"JHT Karyawan",
	"JP Karyawan",
]


def disable_formulas_in_components():
	"""
	Disables formula-based calculation on the master Salary Component doctype.
	"""
	print("\n--- Memulai penonaktifan formula di Salary Components (Master) ---")
	for component_name in COMPONENTS_TO_FIX:
		try:
			if frappe.db.exists("Salary Component", component_name):
				comp_doc = frappe.get_doc("Salary Component", component_name)
				if comp_doc.amount_based_on_formula == 1 or comp_doc.formula:
					print(f"Memperbaiki komponen: '{component_name}'...")
					comp_doc.amount_based_on_formula = 0
					comp_doc.formula = None
					comp_doc.save(ignore_permissions=True)
					print("  -> Formula dinonaktifkan.")
				else:
					print(f"Komponen '{component_name}' sudah benar. Melewati.")
			else:
				print(f"Komponen '{component_name}' tidak ditemukan. Melewati.")
		except Exception as e:
			print(f"❌ GAGAL saat memproses komponen '{component_name}': {e}")
			frappe.log_error(frappe.get_traceback(), "Gagal Menonaktifkan Formula Komponen")
	print("--- Selesai (Salary Components) ---")


def disable_formulas_in_structures():
	"""
	Cancels, amends, and resubmits the target Salary Structure to disable formulas.
	"""
	print("\n--- Memulai perbaikan formula di Salary Structure spesifik ---")

	structure_name = "Struktur Gaji - Tetap"

	if not frappe.db.exists("Salary Structure", structure_name):
		print(f"Salary Structure '{structure_name}' tidak ditemukan.")
		return

	try:
		ss_doc = frappe.get_doc("Salary Structure", structure_name)
		print(f"Memproses Salary Structure: '{ss_doc.name}' (Status: {ss_doc.docstatus})")

		# 1. Cancel the document if it is submitted
		if ss_doc.docstatus == 1:
			ss_doc.cancel()
			print("  -> Dokumen dibatalkan (Cancelled).")

		# 2. Modify the document
		structure_modified = False
		for item in ss_doc.get("earnings", []):
			if item.salary_component in COMPONENTS_TO_FIX and (
				item.amount_based_on_formula == 1 or item.formula
			):
				print(f"  -> Menonaktifkan formula untuk '{item.salary_component}' di tabel Earnings.")
				item.amount_based_on_formula = 0
				item.formula = None
				structure_modified = True

		for item in ss_doc.get("deductions", []):
			if item.salary_component in COMPONENTS_TO_FIX and (
				item.amount_based_on_formula == 1 or item.formula
			):
				print(f"  -> Menonaktifkan formula untuk '{item.salary_component}' di tabel Deductions.")
				item.amount_based_on_formula = 0
				item.formula = None
				structure_modified = True

		# 3. Save and Resubmit if changes were made
		if structure_modified:
			ss_doc.save(ignore_permissions=True)  # Save the changes
			print("  -> Perubahan disimpan.")
			ss_doc.submit()
			print("  -> Dokumen diserahkan kembali (Submitted).")
		else:
			print("  -> Tidak ada formula yang perlu diubah.")
			# If it was cancelled but no changes were needed, resubmit it
			if ss_doc.docstatus == 2:
				ss_doc.submit()
				print("  -> Dokumen diserahkan kembali (Submitted).")

	except Exception as e:
		print(f"❌ GAGAL saat memproses Salary Structure '{structure_name}': {e}")
		frappe.db.rollback()  # Rollback any partial changes
		# Log the full traceback for debugging
		frappe.log_error(frappe.get_traceback(), "Gagal Memperbaiki Salary Structure")
		return  # Stop execution

	print("--- Selesai (Salary Structures) ---")


def run():
	"""Wrapper function to be called by bench execute."""
	frappe.set_user("Administrator")

	disable_formulas_in_components()
	disable_formulas_in_structures()

	frappe.db.commit()
	print("\n✅ Semua perbaikan formula telah selesai.")
