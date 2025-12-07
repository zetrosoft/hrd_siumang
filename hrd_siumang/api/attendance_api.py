import json

import frappe
from frappe.utils import get_datetime


@frappe.whitelist(allow_guest=True)
def sync_employee_checkin():
	"""
	API Endpoint to receive attendance logs from an external application
	and create Employee Checkin documents in Frappe.
	This endpoint must be called via HTTP POST.
	"""
	# --- Security Validation ---
	# In a production environment, these keys should be stored securely
	# in a custom settings DocType or in site_config.json, not hardcoded.
	api_key = frappe.request.headers.get("X-API-Key")
	api_secret = frappe.request.headers.get("X-API-Secret")

	# TODO: Replace with actual credentials fetched from a settings DocType
	expected_api_key = "ganti_dengan_api_key_sebenarnya"
	expected_api_secret = "ganti_dengan_api_secret_sebenarnya"

	if not (api_key == expected_api_key and api_secret == expected_api_secret):
		frappe.response.status_code = 401
		frappe.response["message"] = "Authentication failed: Invalid API credentials."
		return

	# --- Request Body Validation ---
	try:
		data = json.loads(frappe.request.data)
		logs = data.get("logs", [])
	except json.JSONDecodeError:
		frappe.response.status_code = 400
		frappe.response["message"] = "Bad Request: Invalid JSON format."
		return

	if not isinstance(logs, list):
		frappe.response.status_code = 400
		frappe.response["message"] = "Bad Request: 'logs' key must be a list."
		return

	# --- Log Processing ---
	processed_count = 0
	error_logs = []

	for log in logs:
		userid = log.get("userid")
		checktime_str = log.get("checktime")
		checktype = log.get("checktype")

		if not (userid and checktime_str and checktype):
			error_logs.append(
				{"log": log, "error": "Missing required fields (userid, checktime, checktype)."}
			)
			continue

		employee = frappe.db.get_value("Employee", {"attendance_device_id": userid}, "name")
		if not employee:
			error_logs.append({"log": log, "error": f"Employee with device ID '{userid}' not found."})
			continue

		try:
			# Convert timestamp to Frappe's datetime format
			checktime = get_datetime(checktime_str, "%d/%m/%Y %H:%M:%S")

			# Map checktype to Frappe's log_type
			log_type = "IN" if checktype == "I" else "OUT"

			# Create and insert the Employee Checkin document
			doc = frappe.new_doc("Employee Checkin")
			doc.employee = employee
			doc.time = checktime
			doc.log_type = log_type
			# Use ignore_permissions for system-to-system integration
			# This avoids issues if the guest user doesn't have direct permission
			doc.insert(ignore_permissions=True)
			processed_count += 1

		except Exception as e:
			frappe.log_error(message=frappe.get_traceback(), title=f"Error processing log for user {userid}")
			error_logs.append({"log": log, "error": str(e)})

	# Commit all successful insertions to the database
	frappe.db.commit()

	return {
		"status": "completed",
		"processed_count": processed_count,
		"error_count": len(error_logs),
		"errors": error_logs,
	}
