# Copyright (c) 2026, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
from frappe import _, msgprint
from frappe.utils import get_datetime, getdate, time_diff_in_hours


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


@frappe.whitelist()
def get_employees_with_overtime(doctype, txt, searchfield, start, page_len, filters):
	"""
	Returns employees who have submitted Overtime Planning entries.
	Filtered by Payroll Period if provided.
	"""
	conditions = "parent.docstatus = 1"
	if filters.get("payroll_period"):
		period = frappe.get_doc("Payroll Period", filters.get("payroll_period"))
		conditions += f" AND parent.overtime_date BETWEEN '{period.start_date}' AND '{period.end_date}'"

	employees = frappe.db.sql(
		f"""
		SELECT
			DISTINCT detail.employee, emp.employee_name
		FROM
			`tabOvertime Planning Detail` detail
		JOIN
			`tabOvertime Planning` parent ON detail.parent = parent.name
		JOIN
			`tabEmployee` emp ON detail.employee = emp.name
		WHERE
			{conditions} AND (detail.employee LIKE %(txt)s OR emp.employee_name LIKE %(txt)s)
		LIMIT %(start)s, %(page_len)s
	""",
		{"txt": f"%{txt}%", "start": start, "page_len": page_len},
	)
	return employees


def get_columns():
	return [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 180},
		{
			"fieldname": "department",
			"label": _("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "actual_in", "label": _("Actual In"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "actual_out", "label": _("Actual Out"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "total_hours", "label": _("OT Hours"), "fieldtype": "Float", "width": 100},
		{"fieldname": "schema", "label": _("Overtime Schema"), "fieldtype": "Data", "width": 150},
		{
			"fieldname": "overtime_pay_estimated",
			"label": _("Est. Overtime Pay"),
			"fieldtype": "Currency",
			"width": 130,
		},
	]


def get_data(filters):
	data = []
	conditions = "parent.docstatus = 1"

	if filters.get("department"):
		conditions += f" AND parent.department = '{filters.get('department')}'"
	if filters.get("employee"):
		conditions += f" AND detail.employee = '{filters.get('employee')}'"

	if filters.get("payroll_period"):
		period = frappe.get_doc("Payroll Period", filters.get("payroll_period"))
		conditions += f" AND parent.overtime_date BETWEEN '{period.start_date}' AND '{period.end_date}'"

	overtime_records = frappe.db.sql(
		f"""
		SELECT
			detail.employee,
			emp.employee_name,
			parent.department,
			parent.overtime_date as date,
			emp.holiday_list,
			emp.ctc as base_salary,
			parent.name as parent_name
		FROM
			`tabOvertime Planning Detail` AS detail
		JOIN
			`tabOvertime Planning` AS parent ON detail.parent = parent.name
		JOIN
			`tabEmployee` AS emp ON detail.employee = emp.name
		WHERE
			{conditions}
		ORDER BY
			parent.overtime_date ASC, detail.employee ASC
	""",
		as_dict=True,
	)

	skema_cache = {}
	shift_cache = {}

	for record in overtime_records:
		# Fetch actual attendance
		attendance = frappe.db.get_value(
			"Attendance",
			{"employee": record.employee, "attendance_date": record.date, "docstatus": ["<", 2]},
			["in_time", "out_time", "shift"],
			as_dict=True,
		)

		actual_in = attendance.in_time if attendance else None
		actual_out = attendance.out_time if attendance else None

		# Determine if it's holiday
		is_day_holiday = record.holiday_list and is_holiday(record.holiday_list, record.date)

		ot_start_time = None
		ot_end_time = actual_out
		total_hours = 0
		status_message = ""

		if not attendance:
			status_message = _("Attendance not found")
		elif not actual_out:
			status_message = _("Check-out missing")
		else:
			if is_day_holiday:
				skema_name = "Lembur Libur Resmi"
				ot_start_time = actual_in
			else:
				skema_name = "Lembur Hari Kerja"
				shift_type_name = attendance.shift
				if not shift_type_name:
					shift_type_name = frappe.db.get_value(
						"Shift Assignment",
						{"employee": record.employee, "start_date": ["<=", record.date], "status": "Active"},
						"shift_type",
					)

				if shift_type_name:
					if shift_type_name not in shift_cache:
						shift_cache[shift_type_name] = frappe.get_doc("Shift Type", shift_type_name)

					shift_doc = shift_cache[shift_type_name]
					ot_start_time = get_datetime(f"{record.date} {shift_doc.end_time}")

					if get_datetime(ot_start_time) > get_datetime(actual_out):
						status_message = _("Checked out before shift end")
				else:
					status_message = _("No shift assigned")

		if ot_start_time and ot_end_time and not status_message:
			total_hours = time_diff_in_hours(ot_end_time, ot_start_time)
			if total_hours < 0:
				total_hours = 0

		# Calculation
		if not is_day_holiday:
			skema_name = "Lembur Hari Kerja"
		else:
			skema_name = "Lembur Libur Resmi"

		if skema_name not in skema_cache:
			try:
				skema_cache[skema_name] = frappe.get_doc("Overtime Calculation", skema_name)
			except frappe.DoesNotExistError:
				skema_cache[skema_name] = None

		skema_doc = skema_cache[skema_name]
		est_pay = 0
		tooltip_parts = []

		if skema_doc and total_hours > 0:
			base = record.base_salary or 0
			upah_per_jam = base / 173
			jam_tersisa = total_hours
			sorted_rates = sorted(skema_doc.overtime_rates, key=lambda x: x.jam_ke_mulai)

			for rate in sorted_rates:
				if jam_tersisa <= 0:
					break
				jam_mulai = rate.jam_ke_mulai
				jam_selesai = rate.jam_ke_selesai if rate.jam_ke_selesai > 0 else float("inf")
				pengali = rate.pengali_upah
				durasi_layer = (jam_selesai - jam_mulai) + 1 if jam_selesai != float("inf") else float("inf")
				jam_dihitung = min(jam_tersisa, durasi_layer)
				est_pay += jam_dihitung * pengali * upah_per_jam
				tooltip_parts.append(f"{round(jam_dihitung, 2)} jam x {pengali}x")
				jam_tersisa -= jam_dihitung

		if status_message:
			calculation_tooltip = status_message
		else:
			calculation_tooltip = (
				f"{skema_name}: " + ", ".join(tooltip_parts) if tooltip_parts else _("No duration")
			)

		data.append(
			{
				"employee": record.employee,
				"employee_name": record.employee_name,
				"department": record.department,
				"date": record.date,
				"actual_in": actual_in,
				"actual_out": actual_out,
				"total_hours": round(total_hours, 2),
				"schema": skema_name if not status_message else status_message,
				"overtime_pay_estimated": round(est_pay),
				"calculation_tooltip": calculation_tooltip,
			}
		)

	return data
