# hrd_siumang/hrd_siumang/api/fingerspot_driver.py

import frappe
import requests

FINGERSPOT_API_BASE_URL = "https://io.fingerspot.io/api"


def get_scan_log(api_key, start_date, end_date):
	"""Mengambil data scan log dari Fingerspot API."""
	frappe.logger("fingerspot_driver").info(f"Mengambil log dari {start_date} hingga {end_date}")

	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	payload = {"api-key": api_key, "start-date": start_date, "end-date": end_date}

	try:
		response = requests.post(
			f"{FINGERSPOT_API_BASE_URL}/scanlog/get-scanlog", headers=headers, data=payload
		)
		response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

		result = response.json()
		if result.get("status") == "success":
			frappe.logger("fingerspot_driver").info(
				f"Berhasil mendapatkan {len(result.get('data', []))} log."
			)
			return result.get("data", [])
		else:
			frappe.logger("fingerspot_driver").error(f"API Error: {result.get('message')}")
			return []

	except requests.exceptions.RequestException as e:
		frappe.logger("fingerspot_driver").error(f"Request Exception: {e}")
		return []


def process_and_create_checkins(logs):
	"""Memproses log dan membuat dokumen Employee Checkin."""
	created_count = 0
	for log in logs:
		# Cek apakah checkin ini sudah pernah dibuat
		if not frappe.db.exists("Employee Checkin", {"custom_checkin_original_id": log.get("scanlog_id")}):
			# Cari karyawan berdasarkan attendance_device_id
			employee = frappe.db.get_value("Employee", {"attendance_device_id": log.get("pin")}, "name")

			if employee:
				try:
					new_checkin = frappe.new_doc("Employee Checkin")
					new_checkin.employee = employee
					new_checkin.time = log.get("scan_date")
					# Simpan ID asli untuk mencegah duplikasi
					new_checkin.custom_checkin_original_id = log.get("scanlog_id")
					new_checkin.log_type = "IN" if log.get("verify_mode_name") == "check-in" else "OUT"
					new_checkin.insert(ignore_permissions=True)
					created_count += 1
					frappe.logger("fingerspot_driver").info(
						f"Membuat checkin untuk {employee} pada {log.get('scan_date')}"
					)
				except Exception as e:
					frappe.logger("fingerspot_driver").error(f"Gagal membuat checkin: {e}")
			else:
				frappe.logger("fingerspot_driver").warning(
					f"Karyawan dengan PIN/Device ID {log.get('pin')} tidak ditemukan."
				)

	frappe.db.commit()
	frappe.logger("fingerspot_driver").info(f"{created_count} Employee Checkin baru berhasil dibuat.")
