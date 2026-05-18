import frappe
from frappe.utils import getdate


def check_period():
	"""
	Checks if a valid Payroll Period exists for the specified timeframe.
	"""
	company_name = "PT. SIUMANG TEMAN SUKSES"
	start_date_str = "2025-09-01"
	end_date_str = "2025-09-30"

	try:
		frappe.set_user("Administrator")
		print(f"\n--- Memeriksa Payroll Period untuk {company_name} ---")
		print(f"--- Periode: {start_date_str} s/d {end_date_str} ---")

		# Konversi tanggal
		start_date = getdate(start_date_str)
		end_date = getdate(end_date_str)

		payroll_periods = frappe.get_all(
			"Payroll Period",
			filters={
				"company": company_name,
				"start_date": ["<=", start_date],
				"end_date": [">=", end_date],
				"docstatus": 1,  # Harus Submitted
			},
			fields=["name", "start_date", "end_date"],
		)

		print("\n[HASIL PEMERIKSAAN]")
		if not payroll_periods:
			print(
				f"❌ TIDAK DITEMUKAN: Tidak ada 'Payroll Period' yang aktif (Submitted) untuk periode yang mencakup {start_date_str} s/d {end_date_str}."
			)
			print("\n[SOLUSI]")
			print("1. Buka 'Human Resources > Payroll > Payroll Period'.")
			print("2. Klik 'Add Payroll Period'.")
			print(f"3. Isi 'Company', 'Start Date' ({start_date_str}), dan 'End Date' ({end_date_str}).")
			print("4. Simpan (Save) dan Serahkan (Submit) dokumen Payroll Period tersebut.")
			print("5. Setelah itu, coba jalankan 'Process Payroll' lagi.")
		else:
			print("✅ DITEMUKAN: Payroll Period yang valid ada untuk periode ini:")
			for period in payroll_periods:
				print(f"  - Nama: {period.name}, Periode: {period.start_date} s/d {period.end_date}")
			print("\n[KESIMPULAN]")
			print("   Karena Payroll Period sudah ada, masalahnya kemungkinan besar bukan di sini.")
			print("   Penyebab paling mungkin adalah cache atau konfigurasi lain yang lebih dalam.")

	except Exception as e:
		print(f"❌ GAGAL saat menjalankan inspeksi: {e}")


def run():
	"""Wrapper function to be called by bench execute."""
	check_period()
