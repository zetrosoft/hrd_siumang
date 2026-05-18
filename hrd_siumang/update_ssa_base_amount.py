import frappe


def update_ssa_base_amount():
	"""
	Updates the 'base' amount in a specific Salary Structure Assignment (SSA)
	to match the employee's CTC.
	"""
	frappe.set_user("Administrator")  # Ensure permissions

	ssa_name = "HR-SSA-25-11-00737"
	employee_id = "HR-EMP-00003"

	print(f"\n--- Memperbarui Base Amount di SSA: {ssa_name} ---")

	try:
		# Get the employee's CTC
		employee = frappe.get_doc("Employee", employee_id)
		ctc_value = employee.get("ctc")

		if not ctc_value:
			print(
				f"❌ CTC untuk Karyawan '{employee_id}' tidak ditemukan atau 0. Tidak bisa memperbarui SSA."
			)
			return

		# Fetch the SSA document
		ssa = frappe.get_doc("Salary Structure Assignment", ssa_name)

		if ssa.base != ctc_value:
			old_base = ssa.base
			ssa.base = ctc_value
			ssa.save(ignore_permissions=True)
			frappe.db.commit()
			print(
				f"✅ Berhasil memperbarui Base Amount di SSA '{ssa_name}' dari Rp {old_base:,.2f} menjadi Rp {ctc_value:,.2f}."
			)
		else:
			print(
				f"✅ Base Amount di SSA '{ssa_name}' sudah sesuai dengan CTC Karyawan (Rp {ctc_value:,.2f})."
			)

	except frappe.DoesNotExistError:
		print(f"❌ Salary Structure Assignment '{ssa_name}' tidak ditemukan.")
	except Exception as e:
		frappe.db.rollback()
		print(f"❌ Gagal memperbarui SSA '{ssa_name}': {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Memperbarui SSA Base Amount")

	print("---------------------------------------------------\n")
