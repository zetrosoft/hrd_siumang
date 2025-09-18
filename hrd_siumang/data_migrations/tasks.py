# hrd_siumang/hrd_siumang/tasks.py

import frappe
from frappe.utils import add_to_date, nowdate

from .api.fingerspot_driver import get_scan_log, process_and_create_checkins


@frappe.whitelist()
def sync_attendance_logs():
	"""Tugas terjadwal untuk sinkronisasi log absensi dari semua perangkat aktif."""
	frappe.logger("task_sync").info("Memulai sinkronisasi log absensi...")

	active_devices = frappe.get_all(
		"Perangkat Absensi", filters={"status_perangkat": "Aktif"}, fields=["name", "merek", "api_key"]
	)

	for device in active_devices:
		if device.merek == "Fingerspot":
			frappe.logger("task_sync").info(f"Memproses perangkat Fingerspot: {device.name}")

			# Ambil log untuk 1 hari terakhir untuk memastikan tidak ada yang terlewat
			start_date = add_to_date(nowdate(), days=-1, as_string=True)
			end_date = nowdate()

			api_key = frappe.utils.get_password("Perangkat Absensi", device.name, "api_key")
			if not api_key:
				frappe.logger("task_sync").warning(
					f"API Key untuk perangkat {device.name} tidak ditemukan. Melewati..."
				)
				continue

			logs = get_scan_log(api_key, start_date, end_date)
			if logs:
				process_and_create_checkins(logs)
		else:
			frappe.logger("task_sync").info(f"Merek perangkat {device.merek} belum didukung. Melewati...")

	frappe.logger("task_sync").info("Sinkronisasi log absensi selesai.")
