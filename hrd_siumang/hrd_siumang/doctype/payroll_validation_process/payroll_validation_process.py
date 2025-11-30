# Copyright (c) 2025, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_last_day


class PayrollValidationProcess(Document):
	@frappe.whitelist()
	def run_validation(self):
		"""
		Enqueues the background job for validation.
		This is called by the client script.
		"""
		frappe.enqueue(
			"hrd_siumang.doctype.payroll_validation_process.payroll_validation_process.run_validation_task",
			docname=self.name,
			job_user=frappe.session.user,  # Pass the current user
			queue="long",
			timeout=1500,
		)
		return {"status": "enqueued", "job_type": "Validation"}

	@frappe.whitelist()
	def process_absences(self):
		"""
		Enqueues the background job for absence processing.
		This is called by the client script.
		"""
		frappe.enqueue(
			"hrd_siumang.doctype.payroll_validation_process.payroll_validation_process.process_absences_task",
			docname=self.name,
			job_user=frappe.session.user,  # Pass the current user
			queue="long",
			timeout=1500,
		)
		return {"status": "enqueued", "job_type": "Absence Processing"}


# --- Standalone Background Task Functions (NOT whitelisted) ---


def run_validation_task(docname, job_user):
	doc = frappe.get_doc("Payroll Validation Process", docname)

	frappe.logger("PayrollReadiness").info(
		f"Validation Task Started for {doc.company} from {doc.start_date} to {doc.end_date} by user {job_user}"
	)
	frappe.msgprint(_("Starting Payroll Validation..."), title=_("Payroll Validation"), indicator="blue")

	doc.status = "Pending"
	doc.validation_results = []
	doc.save()

	employees = _get_active_employees(doc.company)
	if not employees:
		frappe.msgprint(
			_("No active employees found for the selected company."),
			title=_("Payroll Validation"),
			indicator="orange",
		)
		_create_completion_notification(
			doc, "Validation", "info", _("No active employees found for the selected company."), job_user
		)
		return

	total_employees = len(employees)
	error_found = False

	for i, emp in enumerate(employees):
		frappe.msgprint(
			_("Checking Employee {0} ({1}/{2})...").format(emp.employee_name, i + 1, total_employees),
			title=_("Payroll Validation"),
			indicator="blue",
			alert=False,
		)

		results = []
		results.extend(_check_employee_master_data(emp))
		results.extend(_check_salary_structure_assignment(emp, doc.end_date))
		results.extend(_check_attendance_records(emp, doc.start_date, doc.end_date))

		for res in results:
			doc.append("validation_results", res)
			if res.get("status_icon") == "x":
				error_found = True

	frappe.msgprint(
		_("Finalizing validation results and saving document..."),
		title=_("Payroll Validation"),
		indicator="blue",
		alert=False,
	)
	doc.status = "Errors Found" if error_found else "Validated"
	doc.save()
	frappe.logger("PayrollReadiness").info("Validation Task Finished.")
	_create_completion_notification(doc, "Validation", "error" if error_found else "success", None, job_user)


def process_absences_task(docname, job_user):
	doc = frappe.get_doc("Payroll Validation Process", docname)
	leave_type_to_deduct = "Cuti Tahunan"

	frappe.logger("PayrollReadiness").info(
		f"Absence Processing Task Started for {doc.company} from {doc.start_date} to {doc.end_date} by user {job_user}"
	)
	frappe.msgprint(_("Starting Absence Processing..."), title=_("Absence Processing"), indicator="blue")

	absent_records = frappe.get_all(
		"Attendance",
		filters={
			"status": "Absent",
			"docstatus": 1,
			"company": doc.company,
			"attendance_date": ["between", [doc.start_date, doc.end_date]],
		},
		fields=["name", "employee", "employee_name", "attendance_date"],
	)

	if not absent_records:
		frappe.msgprint(
			_("No 'Absent' records found to process."), title=_("Absence Processing"), indicator="green"
		)
		_create_completion_notification(
			doc, "Absence Processing", "info", _("No 'Absent' records found to process."), job_user
		)
		return

	processed_count = 0
	lwp_count = 0
	error_during_processing = False

	for i, rec in enumerate(absent_records):
		frappe.msgprint(
			_("Processing absence for {0} on {1} ({2}/{3})...").format(
				rec.employee_name, rec.attendance_date, i + 1, len(absent_records)
			),
			title=_("Absence Processing"),
			indicator="blue",
			alert=False,
		)

		leave_balance = _get_leave_balance(rec.employee, leave_type_to_deduct)

		if leave_balance > 0:
			existing_leave = frappe.db.exists(
				"Leave Application",
				{
					"employee": rec.employee,
					"leave_type": leave_type_to_deduct,
					"status": "Approved",
					"docstatus": 1,
					"from_date": ("<=", rec.attendance_date),
					"to_date": (">=", rec.attendance_date),
				},
			)

			if not existing_leave:
				try:
					la = frappe.new_doc("Leave Application")
					la.employee = rec.employee
					la.leave_type = leave_type_to_deduct
					la.from_date = rec.attendance_date
					la.to_date = rec.attendance_date
					la.half_day = 0
					la.reason = (
						"Dibuat otomatis oleh Sistem dari proses Validasi Payroll untuk absensi Alpha."
					)
					la.submit()

					frappe.db.set_value("Attendance", rec.name, "status", "On Leave")
					doc.append(
						"validation_results",
						_create_result(
							frappe._dict(name=rec.employee, employee_name=rec.employee_name),
							"Absence Processed",
							"check",
							f"Leave Application created for {rec.attendance_date}.",
						),
					)
					processed_count += 1
				except Exception as e:
					doc.append(
						"validation_results",
						_create_result(
							frappe._dict(name=rec.employee, employee_name=rec.employee_name),
							"Absence Processing Failed",
							"x",
							f"Failed to create Leave Application for {rec.attendance_date}: {e}",
						),
					)
					error_during_processing = True
			else:
				frappe.db.set_value("Attendance", rec.name, "status", "On Leave")
				doc.append(
					"validation_results",
					_create_result(
						frappe._dict(name=rec.employee, employee_name=rec.employee_name),
						"Absence Processed",
						"check",
						f"Attendance for {rec.attendance_date} synced with existing leave.",
					),
				)
		else:
			doc.append(
				"validation_results",
				_create_result(
					frappe._dict(name=rec.employee, employee_name=rec.employee_name),
					"Absence as LWP",
					"alert-triangle",
					f"No leave balance for {rec.attendance_date}. Will be treated as LWP.",
				),
			)
			lwp_count += 1

	doc.save()
	_create_completion_notification(
		doc,
		"Absence Processing",
		"error" if error_during_processing else "success",
		_("Absence processing complete. {0} records converted to leave, {1} records marked as LWP.").format(
			processed_count, lwp_count
		),
		job_user,
	)


# --- Standalone Helper Functions ---


def _create_completion_notification(doc, job_type, status, custom_message=None, for_user=None):
	"""Creates a Notification Log entry upon job completion."""
	target_user = for_user or frappe.session.user  # Fallback to current session user if not provided

	if status == "success":
		subject = _("{0} Completed Successfully").format(job_type)
		message = custom_message or _(
			"Your {0} for {1} has been completed successfully. Click to view results."
		).format(job_type, doc.name)
		color = "green"
	elif status == "error":
		subject = _("{0} Completed with Errors").format(job_type)
		message = custom_message or _(
			"Your {0} for {1} has encountered errors. Click to view details and resolve."
		).format(job_type, doc.name)
		color = "red"
	else:  # info
		subject = _("{0} Status Update").format(job_type)
		message = custom_message or _("Your {0} for {1} has finished. Click to view details.").format(
			job_type, doc.name
		)
		color = "blue"

	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"document_type": doc.doctype,
			"document_name": doc.name,
			"for_user": target_user,
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"type": "Alert",
			"color": color,  # This field might not exist in standard Frappe Notification Log, but useful for custom styling.
		}
	).insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.commit()
	# Also push a real-time message if the user is online
	frappe.publish_realtime("msgprint", frappe.utils.html2text(message), user=target_user)


def _get_active_employees(company):
	return frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		fields=["name", "employee_name", "department", "designation", "bank_ac_no"],
	)


def _create_result(employee, check_type, icon, details):
	return {
		"employee": employee.name,
		"check_description": check_type,
		"status_icon": icon,
		"details": details,
		"resolution_link": employee.name,
	}


def _check_employee_master_data(employee):
	results = []
	if not employee.department:
		results.append(_create_result(employee, "Master Data", "x", "Employee is missing Department."))
	if not employee.designation:
		results.append(_create_result(employee, "Master Data", "x", "Employee is missing Designation."))
	if not employee.bank_ac_no:
		results.append(_create_result(employee, "Master Data", "x", "Employee is missing Bank Account No."))
	if not results:
		results.append(_create_result(employee, "Master Data", "check", "All master data is complete."))
	return results


def _check_salary_structure_assignment(employee, end_date):
	if frappe.db.exists(
		"Salary Structure Assignment",
		{"employee": employee.name, "docstatus": 1, "from_date": ("<=", end_date)},
	):
		return [_create_result(employee, "Salary Structure", "check", "Active assignment found.")]
	else:
		return [
			_create_result(
				employee,
				"Salary Structure",
				"x",
				"No active Salary Structure Assignment found for this period.",
			)
		]


def _check_attendance_records(employee, start_date, end_date):
	absent_days = frappe.db.count(
		"Attendance",
		{
			"employee": employee.name,
			"status": "Absent",
			"attendance_date": ["between", [start_date, end_date]],
		},
	)
	if absent_days > 0:
		return [
			_create_result(
				employee,
				"Attendance",
				"alert-triangle",
				f"{absent_days} 'Absent' records found. Run 'Process Absences' to convert them to leave.",
			)
		]
	else:
		return [_create_result(employee, "Attendance", "check", "No 'Absent' records found.")]


def _get_leave_balance(employee, leave_type):
	today = frappe.utils.today()
	latest_entry = frappe.get_all(
		"Leave Ledger Entry",
		filters={"employee": employee, "leave_type": leave_type, "transaction_date": ("<=", today)},
		fields=["closing_balance"],
		order_by="transaction_date desc, creation desc",
		limit=1,
	)
	if latest_entry:
		return latest_entry[0].closing_balance
	allocation = frappe.get_all(
		"Leave Allocation",
		filters={
			"employee": employee,
			"leave_type": leave_type,
			"docstatus": 1,
			"from_date": ("<=", today),
			"to_date": (">=", today),
		},
		fields=["new_leaves_allocated"],
	)
	return sum(alloc.new_leaves_allocated for alloc in allocation)
