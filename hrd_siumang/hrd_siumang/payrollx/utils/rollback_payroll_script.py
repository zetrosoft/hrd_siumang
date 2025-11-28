# Skrip Rollback Modular untuk Migrasi Payroll
# Dijalankan dari `bench console`
# PERHATIAN: Skrip ini akan menghapus data secara permanen. Gunakan dengan hati-hati.

import time

import frappe

# ==== FUNGSI-FUNGSI UTAMA (UNTUK DIPANGGIL DARI CONSOLE) ====


def rollback_ter_doctype(dry_run=False):
	"""Menghapus Doctype Tarif Efektif Rata-rata."""
	doctype_name = "Tarif Efektif Rata-rata"
	if frappe.db.exists("DocType", doctype_name):
		if dry_run:
			print(f"[DRY RUN] Akan menghapus Doctype: '{doctype_name}'")
		else:
			try:
				frappe.delete_doc("DocType", doctype_name, ignore_permissions=True, force=True)
				print(f"✅ BERHASIL: Doctype '{doctype_name}' dihapus.")
			except Exception as e:
				print(f"❌ GAGAL saat menghapus Doctype '{doctype_name}': {e}")
	else:
		print(f"[INFO] Doctype '{doctype_name}' tidak ditemukan.")


def rollback_step0_slips(dry_run=False):
	"""LANGKAH 0: Membatalkan dan menghapus Salary Slips."""
	mode = "DRY RUN" if dry_run else "LIVE RUN"
	print(f"\n--- [ROLLBACK 0] Menghapus Salary Slips ({mode}) ---")

	slips = frappe.get_all("Salary Slip", filters=[["name", "like", "Sal Slip/%"]])

	if not slips:
		print("[INFO] Tidak ada Salary Slip yang relevan untuk dihapus.")
		return

	for item in slips:
		slip_name = item.name
		if dry_run:
			print(f"[DRY RUN] Akan membatalkan dan menghapus Salary Slip: '{slip_name}'")
			continue

		try:
			doc = frappe.get_doc("Salary Slip", slip_name)
			if doc.docstatus == 1:  # Submitted
				doc.cancel()
			frappe.delete_doc("Salary Slip", slip_name, force=1, ignore_permissions=True)
			print(f"✅ BERHASIL: Salary Slip '{slip_name}' dibatalkan dan dihapus.")
		except Exception as e:
			print(f"❌ GAGAL saat menghapus Salary Slip '{slip_name}': {e}")
			frappe.db.rollback()
			return

	if not dry_run:
		frappe.db.commit()
	print("--- [ROLLBACK 0] Selesai ---")


def rollback_step3_assignments(dry_run=False):
	"""LANGKAH 1 (Urutan Terbalik): Membatalkan dan menghapus Salary Structure Assignments."""
	mode = "DRY RUN" if dry_run else "LIVE RUN"
	print(f"\n--- [ROLLBACK 3] Menghapus Assignments ({mode}) ---")

	# Cari assignment yang terhubung ke struktur yang kita buat
	assignments = frappe.db.sql(
		"""
        SELECT sa.name
        FROM `tabSalary Structure Assignment` sa
        JOIN `tabSalary Structure` ss ON sa.salary_structure = ss.name
        WHERE ss.name LIKE 'Struktur Gaji - %' AND sa.docstatus = 1
    """,
		as_dict=1,
	)

	if not assignments:
		print("[INFO] Tidak ada Salary Structure Assignment yang relevan untuk dihapus.")
		return

	for item in assignments:
		assignment_name = item.name
		if dry_run:
			print(f"[DRY RUN] Akan membatalkan dan menghapus Assignment: '{assignment_name}'")
			continue

		try:
			doc = frappe.get_doc("Salary Structure Assignment", assignment_name)
			if doc.docstatus == 1:
				doc.cancel()
			frappe.delete_doc(
				"Salary Structure Assignment", assignment_name, force=1, ignore_permissions=True
			)
			print(f"✅ BERHASIL: Assignment '{assignment_name}' dibatalkan dan dihapus.")
		except Exception as e:
			print(f"❌ GAGAL saat menghapus assignment '{assignment_name}': {e}")
			frappe.db.rollback()
			return

	if not dry_run:
		frappe.db.commit()
	print("--- [ROLLBACK 3] Selesai ---")


def rollback_step2_structures(dry_run=False):
	"""LANGKAH 2 (Urutan Terbalik): Menghapus Salary Structures."""
	mode = "DRY RUN" if dry_run else "LIVE RUN"
	print(f"\n--- [ROLLBACK 2] Menghapus Structures ({mode}) ---")

	structures = frappe.get_all("Salary Structure", filters=[["name", "like", "Struktur Gaji - %"]])

	if not structures:
		print("[INFO] Tidak ada Salary Structure yang relevan untuk dihapus.")
		return

	for item in structures:
		structure_name = item.name
		if dry_run:
			print(f"[DRY RUN] Akan menghapus Salary Structure: '{structure_name}'")
			continue

		try:
			# Ambil dokumen untuk memeriksa status
			doc = frappe.get_doc("Salary Structure", structure_name)
			if doc.docstatus == 1:
				doc.cancel()

			# Setelah dibatalkan (atau jika statusnya draft), baru dihapus
			frappe.delete_doc("Salary Structure", structure_name, force=1, ignore_permissions=True)
			print(f"✅ BERHASIL: Salary Structure '{structure_name}' dihapus.")
		except Exception as e:
			print(f"❌ GAGAL saat menghapus structure '{structure_name}': {e}")
			frappe.db.rollback()
			return

	if not dry_run:
		frappe.db.commit()
	print("--- [ROLLBACK 2] Selesai ---")


def rollback_step1_components(dry_run=False):
	"""LANGKAH 3 (Urutan Terbalik): Menghapus Salary Components."""
	mode = "DRY RUN" if dry_run else "LIVE RUN"
	print(f"\n--- [ROLLBACK 1] Menghapus Components ({mode}) ---")

	components_to_delete = [
		"Gaji Pokok",
		"Tunjangan Jabatan",
		"Tunjangan Komunikasi",
		"Tunjangan Lain",
		"Tunjangan Transport",
		"Tunjangan Makan",
		"Overtime",
		"Rapel",
		"JHT Perusahaan",
		"JKK Perusahaan",
		"JKM Perusahaan",
		"JP Perusahaan",
		"JKN Perusahaan",
		"Potongan Absensi",
		"Potongan Lain-lain",
		"JHT Karyawan",
		"JP Karyawan",
		"JKN Karyawan",
		"PPh 21",
	]

	for comp_name in components_to_delete:
		if frappe.db.exists("Salary Component", comp_name):
			if dry_run:
				print(f"[DRY RUN] Akan menghapus Salary Component: '{comp_name}'")
				continue

			try:
				frappe.delete_doc("Salary Component", comp_name, force=1, ignore_permissions=True)
				print(f"✅ BERHASIL: Salary Component '{comp_name}' dihapus.")
			except Exception as e:
				print(f"❌ GAGAL saat menghapus component '{comp_name}': {e}")
				frappe.db.rollback()
				return
		else:
			if dry_run:
				print(f"[INFO] Salary Component '{comp_name}' tidak ditemukan.")

	if not dry_run:
		frappe.db.commit()
	print("--- [ROLLBACK 1] Selesai ---")


# ==== FUNGSI EKSEKUSI UTAMA ====


def test_rollback():
	"""Menjalankan simulasi (dry run) untuk semua langkah rollback."""
	rollback_step0_slips(dry_run=True)
	rollback_step3_assignments(dry_run=True)
	rollback_step2_structures(dry_run=True)
	rollback_step1_components(dry_run=True)
	print("\n✅ Simulasi Rollback Selesai. Tidak ada data yang diubah.")


def run_full_rollback():
	"""Menjalankan semua langkah rollback secara live. PERHATIAN: Ini akan menghapus data permanen."""
	print("PERINGATAN: Anda akan menghapus data payroll yang telah dibuat.")
	print("Proses akan dimulai dalam 5 detik...")
	time.sleep(5)

	frappe.set_user("Administrator")
	rollback_step0_slips(dry_run=False)
	rollback_step3_assignments(dry_run=False)
	rollback_step2_structures(dry_run=False)
	rollback_step1_components(dry_run=False)
	print("\n✅ Semua langkah rollback telah selesai dijalankan.")


print(
	"Skrip rollback telah dimuat. Panggil fungsi yang Anda butuhkan, contoh: test_rollback() atau run_full_rollback()"
)
