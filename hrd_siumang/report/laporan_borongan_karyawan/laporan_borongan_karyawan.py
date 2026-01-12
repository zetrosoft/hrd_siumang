# Copyright (c) 2026, Siumang and contributors
# For license information, please see license.txt
# Trivial change to force reload: 2026-01-12 16:00:00

from calendar import monthrange
from datetime import datetime, timedelta

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	# Add Total row at the end
	if len(data) > 1:
		data.append(get_total_row(data, columns))

	return columns, data


def get_columns(filters):
	month_filter = filters.get("bulan")
	year, month = (
		datetime.strptime(month_filter, "%Y-%m-%d").year,
		datetime.strptime(month_filter, "%Y-%m-%d").month,
	)

	num_days = monthrange(year, month)[1]

	columns = [
		{
			"label": _("Nama Karyawan"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 200,
		}
	]

	for day in range(1, num_days + 1):
		columns.append(
			{
				"label": str(day),
				"fieldname": "day_" + str(day),
				"fieldtype": "Currency",
				"width": 100,
			}
		)

	columns.append(
		{
			"label": _("Total Karyawan"),
			"fieldname": "total_karyawan",
			"fieldtype": "Currency",
			"width": 150,
		}
	)

	return columns


def get_data(filters):
	# Get start and end dates of the month
	month_filter = filters.get("bulan")
	start_date = datetime.strptime(month_filter, "%Y-%m-%d").replace(day=1)
	num_days = monthrange(start_date.year, start_date.month)[1]
	end_date = start_date.replace(day=num_days)

	# Base conditions
	conditions = {
		"docstatus": 1,
		"posting_date": ["between", [start_date, end_date]],
	}
	if filters.get("pekerjaan_borongan"):
		# Get pekerjaan_borongan from the parent doctype
		conditions["pekerjaan_borongan"] = filters.get("pekerjaan_borongan")

	# Fetch all relevant entries
	hasil_borongan = frappe.get_all(
		"Detail Hasil Borongan",
		fields=[
			"parent",
			"tipe_penerima_tugas",
			"karyawan",
			"total_harga_item",
		],
		filters={"parent": ["in", frappe.get_all("Input Hasil Borongan", filters=conditions, pluck="name")]},
	)

	# Fetch team members
	teams = frappe.get_all("Tim Borongan", fields=["name"])
	team_members_map = {}
	for team in teams:
		team_doc = frappe.get_doc("Tim Borongan", team.name)
		members = [d.karyawan for d in team_doc.get("anggota_tim")]
		team_members_map[team.name] = members

	# Process data
	employee_earnings = {}
	for entry in hasil_borongan:
		parent_doc = frappe.get_doc("Input Hasil Borongan", entry.parent)
		day = parent_doc.posting_date.day

		if entry.tipe_penerima_tugas == "Individu" and entry.karyawan:
			employee_list = [entry.karyawan]
			amount_per_employee = entry.total_harga_item
		elif entry.tipe_penerima_tugas == "Tim" and entry.karyawan in team_members_map:
			employee_list = team_members_map[entry.karyawan]
			if not employee_list:
				continue
			amount_per_employee = entry.total_harga_item / len(employee_list)
		else:
			continue

		for emp in employee_list:
			if emp not in employee_earnings:
				employee_earnings[emp] = {}
			day_key = f"day_{day}"
			employee_earnings[emp][day_key] = employee_earnings[emp].get(day_key, 0) + amount_per_employee

	# Format data for report
	report_data = []

	# Get all employee names in one go
	employee_ids = list(employee_earnings.keys())
	employee_names_map = {}
	if employee_ids:
		employees = frappe.get_all(
			"Employee", filters={"name": ["in", employee_ids]}, fields=["name", "employee_name"]
		)
		employee_names_map = {emp.name: emp.employee_name for emp in employees}

	for emp, earnings in employee_earnings.items():
		row = {
			"employee_name": employee_names_map.get(emp, emp),
		}
		total_karyawan = 0
		for day_key, amount in earnings.items():
			row[day_key] = amount
			total_karyawan += amount
		row["total_karyawan"] = total_karyawan
		report_data.append(row)

	return sorted(report_data, key=lambda x: x["employee_name"])


def get_total_row(data, columns):
	total_row = {"employee_name": "<b>" + _("Total Harian") + "</b>"}
	for col in columns:
		if col["fieldname"] not in ["employee_name"]:
			total = sum(row.get(col["fieldname"], 0) for row in data)
			total_row[col["fieldname"]] = total
	return total_row
