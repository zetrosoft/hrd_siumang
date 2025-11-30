# Copyright (c) 2025, Bijak Techno and contributors
# For license information, please see license.txt

from datetime import timedelta  # Import timedelta for date calculations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

# Import fingerspot_driver functions
# Assuming fingerspot_driver.py will be moved to hrd_siumang/utils/fingerspot_integration
from hrd_siumang.utils.fingerspot_integration import get_scan_log, process_and_create_checkins


class FingerspotIntegrationLog(Document):
	def validate(self):
		if self.sync_frequency == "Specific Times" and not self.specific_sync_times:
			frappe.throw(
				_("Please add at least one specific sync time when 'Sync Frequency' is 'Specific Times'.")
			)

	@frappe.whitelist()
	def sync_fingerspot_data(self, start_date=None, end_date=None):
		# Ensure only one sync process runs at a time for this DocType
		if frappe.cache().get_value(f"fingerspot_sync_in_progress:{self.name}"):
			frappe.msgprint(_("Fingerspot sync is already in progress. Please wait."), indicator="orange")
			return {"status": "error", "message": "Sync already in progress."}

		frappe.cache().set_value(
			f"fingerspot_sync_in_progress:{self.name}", True, expires_in_sec=1800
		)  # 30 mins timeout

		current_sync_datetime = now_datetime()
		self.status_message = _("Sync started at {0}...").format(
			current_sync_datetime.strftime("%Y-%m-%d %H:%M:%S")
		)
		self.save(ignore_permissions=True)
		frappe.db.commit()

		try:
			# Determine start_date and end_date for scan log retrieval
			# Default to yesterday for daily sync, or last_sync_datetime
			if not start_date:
				# Use last_sync_datetime if available, otherwise default to 1 day before now
				default_start_date = (get_datetime(now_datetime()) - timedelta(days=1)).strftime("%Y-%m-%d")
				start_date = (
					self.last_sync_datetime.strftime("%Y-%m-%d")
					if self.last_sync_datetime
					else default_start_date
				)
			if not end_date:
				end_date = now_datetime().strftime("%Y-%m-%d")

			frappe.logger("fingerspot_integration").info(
				f"Initiating Fingerspot sync from {start_date} to {end_date} for API Key {self.api_key[:5]}..."
			)

			# 1. Get Scan Logs from Fingerspot API
			# Pass fingerspot_api_base_url
			scan_logs = get_scan_log(self.api_key, start_date, end_date, self.fingerspot_api_base_url)

			# 2. Process and Create Employee Checkins
			created_count = process_and_create_checkins(scan_logs)

			# 3. Update DocType Status and Log History
			self.last_sync_datetime = current_sync_datetime
			self.status_message = _("Sync completed successfully. {0} new checkins processed.").format(
				created_count
			)
			self.append(
				"sync_history",
				{
					"sync_datetime": current_sync_datetime,
					"status": "Success",
					"message": _("{0} new checkins processed.").format(created_count),
					"records_processed": created_count,
				},
			)
			self.save(ignore_permissions=True)
			frappe.db.commit()

			frappe.logger("fingerspot_integration").info(self.status_message)
			frappe.msgprint(_("Fingerspot sync completed."), indicator="green")
			return {"status": "success", "message": self.status_message, "records_processed": created_count}

		except Exception as e:
			error_message = _("Fingerspot sync failed: {0}").format(frappe.get_traceback())
			self.status_message = error_message
			self.append(
				"sync_history",
				{
					"sync_datetime": current_sync_datetime,
					"status": "Failed",
					"message": frappe.utils.cstr(e)[:140],  # Limit message length
					"records_processed": 0,
				},
			)
			self.save(ignore_permissions=True)
			frappe.db.rollback()  # Rollback any partial changes if error occurred
			frappe.logger("fingerspot_integration").error(error_message)
			frappe.msgprint(_("Fingerspot sync failed. Check error log."), indicator="red")
			return {"status": "error", "message": frappe.utils.cstr(e)}
		finally:
			frappe.cache().delete_value(f"fingerspot_sync_in_progress:{self.name}")

	@frappe.whitelist()
	def get_scheduled_times(self):
		if self.sync_frequency == "Specific Times":
			return [time_item.sync_time for time_item in self.specific_sync_times]
		return []


# Helper function for scheduler, as it's not a DocType method
@frappe.whitelist()
def run_fingerspot_sync_from_scheduler():
	# This function will be called by scheduler
	fingerspot_settings = frappe.get_single("Fingerspot Integration Log")
	if fingerspot_settings.enable_auto_sync:
		if fingerspot_settings.sync_frequency == "Hourly":
			frappe.enqueue(fingerspot_settings.sync_fingerspot_data, timeout=1800)
		elif fingerspot_settings.sync_frequency == "Daily":
			# For daily, we can enqueue once a day, or if called hourly, check if it's already run today
			frappe.enqueue(fingerspot_settings.sync_fingerspot_data, timeout=1800)
		elif fingerspot_settings.sync_frequency == "Specific Times":
			current_time = now_datetime().time()
			for scheduled_time_str in fingerspot_settings.get_scheduled_times():
				scheduled_time = get_datetime(scheduled_time_str).time()
				# Check if current time is close to scheduled time (e.g., within a few minutes)
				# This needs refinement to avoid multiple triggers within the same hour
				if (
					abs(
						(current_time.hour * 60 + current_time.minute)
						- (scheduled_time.hour * 60 + scheduled_time.minute)
					)
					< 5
				):
					# Check if already synced for this specific time today
					# This check needs to be more robust for production
					frappe.enqueue(fingerspot_settings.sync_fingerspot_data, timeout=1800)
					break
