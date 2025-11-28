import math

import frappe
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
from frappe import _


@frappe.whitelist()
def calculate_pph21(doc, method=None):
	"""
	Menghitung PPh 21 bulanan untuk seorang karyawan berdasarkan data pada Salary Slip
	menggunakan metode Tarif Efektif Rerata (TER).
	"""
	try:
		# 1. Ambil Data Karyawan
		employee = frappe.get_doc("Employee", doc.employee)
		status_ptkp = employee.status_pajak
		total_pendapatan_bruto_bulanan = doc.gross_pay

		frappe.msgprint(f"DEBUG PPH: Karyawan: {employee.name}")
		frappe.msgprint(f"DEBUG PPH: Status PTKP: {status_ptkp}")
		frappe.msgprint(f"DEBUG PPH: Total Pendapatan Bruto Bulanan: {total_pendapatan_bruto_bulanan}")

		# 2. Tentukan Kategori TER (ini adalah simplifikasi, bisa diperluas)
		# Kategori A: TK/0, TK/1, K/0
		# Kategori B: TK/2, TK/3, K/1, K/2
		# Kategori C: K/3
		if status_ptkp in ["TK/2", "TK/3", "K/1", "K/2"]:
			kategori_ter = "B"
		elif status_ptkp == "K/3":
			kategori_ter = "C"
		else:
			kategori_ter = "A"
		frappe.msgprint(f"DEBUG PPH: Kategori TER ditentukan: {kategori_ter}")

		# 3. Dapatkan tarif TER dari DocType 'Tarif Efektif Rerata'
		filters = {
			"kategori_ter": kategori_ter,
			"batas_penghasilan_bruto_bulanan_bawah": ["<=", total_pendapatan_bruto_bulanan],
			"batas_penghasilan_bruto_bulanan_atas": [">=", total_pendapatan_bruto_bulanan],
		}
		frappe.msgprint(f"DEBUG PPH: Filter yang digunakan untuk mencari TER: {filters}")

		ter_item = frappe.get_list(
			"Tarif Efektif Rerata",
			filters=filters,
			fields=[
				"tarif_ter",
				"batas_penghasilan_bruto_bulanan_bawah",
				"batas_penghasilan_bruto_bulanan_atas",
			],
			limit=1,
		)

		if not ter_item:
			frappe.msgprint(
				f"DEBUG PPH: Tarif TER TIDAK ditemukan untuk Karyawan {employee.name}, Kategori {kategori_ter}, Bruto Bulanan {total_pendapatan_bruto_bulanan}. Mengembalikan 0."
			)
			frappe.log_error(
				f"Tarif TER tidak ditemukan untuk Karyawan {employee.name}, Kategori {kategori_ter}, Bruto Bulanan {total_pendapatan_bruto_bulanan}"
			)
			return 0

		ter_rate_percent = ter_item[0].tarif_ter
		ter_rate = ter_rate_percent / 100

		frappe.msgprint(f"DEBUG PPH: Tarif TER ditemukan. Persen: {ter_rate_percent}%, Rate: {ter_rate}")
		frappe.msgprint(
			f"DEBUG PPH: Rentang TER: Bawah={ter_item[0].batas_penghasilan_bruto_bulanan_bawah}, Atas={ter_item[0].batas_penghasilan_bruto_bulanan_atas}"
		)
		frappe.msgprint(f"DEBUG PPH: Menggunakan metode PPh 21 TER dengan tarif: {ter_rate*100}%")

		# 4. Hitung PPh 21 Bulanan
		pph21_bulanan = total_pendapatan_bruto_bulanan * ter_rate

		frappe.msgprint(f"DEBUG PPH: PPh 21 Bulanan (sebelum pembulatan): {pph21_bulanan}")

		return round(pph21_bulanan)

	except Exception as e:
		frappe.msgprint(f"DEBUG PPH: Exception caught: {e}")
		frappe.log_error(frappe.get_traceback(), "Kalkulasi PPh 21 Gagal")
		return 0


@frappe.whitelist()
def calculate_overtime(doc, method=None):
	"""
	Menghitung total pendapatan lembur secara dinamis berdasarkan Overtime Planning.
	Skema lembur dipilih otomatis berdasarkan hari kerja vs hari libur.
	"""
	try:
		# 1. Ambil data dari Salary Slip dan Employee
		employee_id = doc.employee
		start_date = doc.start_date
		end_date = doc.end_date

		employee_doc = frappe.get_doc("Employee", employee_id)
		holiday_list_name = employee_doc.holiday_list
		if not holiday_list_name:
			frappe.log_error(f"Karyawan {employee_id} tidak memiliki Holiday List.", "Kalkulasi Lembur Gagal")
			return 0

		# 2. Query semua record lembur yang relevan
		overtime_records = frappe.db.sql(
			f"""
            SELECT
                detail.start_time,
                detail.end_time,
                parent.overtime_date
            FROM
                `tabOvertime Planning Detail` AS detail
            JOIN
                `tabOvertime Planning` AS parent ON detail.parent = parent.name
            WHERE
                detail.employee = '{employee_id}'
                AND parent.docstatus = 1
                AND parent.overtime_date BETWEEN '{start_date}' AND '{end_date}'
        """,
			as_dict=True,
		)

		if not overtime_records:
			return 0

		# 3. Hitung upah per jam satu kali
		gaji_sebulan = doc.base
		if not gaji_sebulan:
			frappe.throw(_("Gaji Pokok (Base) tidak ditemukan untuk Karyawan {0}").format(doc.employee_name))
		upah_per_jam = (1 / 173) * gaji_sebulan

		# 4. Inisialisasi skema dan total pendapatan
		# Cache skema agar tidak query berulang kali di dalam loop
		skema_cache = {}
		total_pendapatan_lembur = 0
		from frappe.utils import time_diff_in_hours

		# 5. Loop setiap record lembur untuk dihitung
		for record in overtime_records:
			if not (record.start_time and record.end_time and record.overtime_date):
				continue

			jam_lembur_record = time_diff_in_hours(record.end_time, record.start_time)
			if not jam_lembur_record > 0:
				continue

			# LOGIKA CERDAS: Tentukan skema berdasarkan tanggal
			if is_holiday(holiday_list_name, record.overtime_date):
				skema_name = "Lembur Libur Resmi"
			else:
				skema_name = "Lembur Hari Kerja"

			# Ambil skema dari cache atau query baru jika belum ada
			if skema_name not in skema_cache:
				try:
					skema_cache[skema_name] = frappe.get_doc("Overtime Calculation", skema_name)
				except frappe.DoesNotExistError:
					frappe.throw(_("Skema Lembur dengan nama '{0}' tidak ditemukan.").format(skema_name))

			skema_doc = skema_cache[skema_name]

			# Hitung pendapatan untuk record ini
			pendapatan_record = 0
			jam_tersisa = jam_lembur_record
			sorted_rates = sorted(skema_doc.overtime_rates, key=lambda x: x.jam_ke_mulai)

			for rate in sorted_rates:
				if jam_tersisa <= 0:
					break

				jam_mulai = rate.jam_ke_mulai
				jam_selesai = rate.jam_ke_selesai if rate.jam_ke_selesai > 0 else float("inf")
				pengali = rate.pengali_upah
				durasi_layer = (jam_selesai - jam_mulai) + 1 if jam_selesai != float("inf") else float("inf")
				jam_dihitung = min(jam_tersisa, durasi_layer)

				pendapatan_record += jam_dihitung * pengali * upah_per_jam
				jam_tersisa -= jam_dihitung

			total_pendapatan_lembur += pendapatan_record

		return round(total_pendapatan_lembur)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Kalkulasi Lembur Gagal")
		return 0
