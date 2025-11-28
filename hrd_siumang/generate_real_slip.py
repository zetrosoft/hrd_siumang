# Copyright (c) 2025, PT. SIUMANG TEMAN SUKSES and contributors
# For license information, please see license.txt

from datetime import date, timedelta

import frappe
from frappe.model.document import Document


def generate_slip(employee_id="HR-EMP-00003", month=6, year=2025):
	"""
	Generates a new Salary Slip for a specific employee and period.
	This function will delete any existing submitted slip for the same period
	to ensure a clean test.
	"""
	frappe.set_user("Administrator")
	print(f"--- Memulai pembuatan Salary Slip untuk Karyawan: {employee_id} ---")

	# --- 1. Define Period ---
	start_date = date(year, month, 1)
	# Simple logic to get the last day of the month
	end_date = date(year, month, 28) + timedelta(days=4)
	end_date = end_date - timedelta(days=end_date.day)

	print(f"Periode: {start_date.strftime('%d-%m-%Y')} s/d {end_date.strftime('%d-%m-%Y')}")

	# --- 2. Clean Up Existing Slips for the Same Period ---
	existing_slips = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": employee_id,
			"start_date": start_date,
			"end_date": end_date,
			"docstatus": ["!=", 2],  # Do not delete cancelled slips
		},
	)

	if existing_slips:
		print(f"Ditemukan {len(existing_slips)} slip yang ada untuk periode ini. Menghapus...")
		for slip_data in existing_slips:
			try:
				slip = frappe.get_doc("Salary Slip", slip_data.name)
				if slip.docstatus == 1:
					slip.cancel()
				frappe.delete_doc("Salary Slip", slip_data.name, force=1, ignore_permissions=True)
				print(f"  - Slip '{slip_data.name}' dihapus.")
			except Exception as e:
				print(f"  - Gagal menghapus slip '{slip_data.name}': {e}")
		frappe.db.commit()  # Commit deletion

	# --- 3. Get Active Salary Structure Assignment ---
	try:
		ssa = frappe.get_doc("Salary Structure Assignment", {"employee": employee_id, "docstatus": 1})
		print(f"Menggunakan Salary Structure Assignment: '{ssa.name}' (Structure: {ssa.salary_structure})")
	except frappe.DoesNotExistError:
		print(
			f"❌ GAGAL: Tidak ada Salary Structure Assignment aktif yang ditemukan untuk karyawan {employee_id}."
		)
		return

	# --- 4. Create and Process New Salary Slip ---
	try:
		print("Membuat dokumen Salary Slip baru...")
		new_slip = frappe.new_doc("Salary Slip")
		new_slip.employee = employee_id
		new_slip.start_date = start_date
		new_slip.end_date = end_date
		new_slip.salary_structure = ssa.salary_structure

		# The 'calculate_payroll_components' function will be triggered on save
		print("Menyimpan dokumen untuk memicu kalkulasi komponen...")
		new_slip.save(ignore_permissions=True)

		print("Menyerahkan (Submit) Salary Slip...")
		new_slip.submit()

		frappe.db.commit()
		print(f"✅ BERHASIL: Salary Slip '{new_slip.name}' telah dibuat dan diserahkan.")
		print("Anda sekarang dapat melihatnya di sistem atau mencetaknya.")

	except Exception as e:
		frappe.db.rollback()
		print(f"❌ GAGAL saat membuat atau menyerahkan Salary Slip: {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Generate Real Slip")
		print("Detail error telah dicatat di 'Error Log'.")


def run():
	"""Wrapper function to be called by bench execute."""
	generate_slip()
