# Copyright (c) 2026, Siumang and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder.functions import Match


class AnggotaTimBorongan(Document):
	pass


@frappe.whitelist()
def employee_query(doctype, txt, searchfield, start, page_len, filters):
	frappe.log_by_ajax(f"DEBUG: employee_query called with doctype={doctype}, txt={txt}, filters={filters}")

	# Ensure filters is a dictionary, even if not provided
	filters = filters if filters is not None else {}

	# Add our custom filter for employee_type
	filters["employee_type"] = "Harian"
	frappe.log_by_ajax(f"DEBUG: employee_query - Modified filters: {filters}")

	# Construct the query using frappe.get_list for better compatibility and safety
	employee_list = frappe.get_list(
		"Employee",
		filters=filters,
		fields=["name", "employee_name"],
		or_filters={"name": ("like", f"%{txt}%"), "employee_name": ("like", f"%{txt}%")},
		limit_start=start,
		limit_page_length=page_len,
		order_by="employee_name ASC",
	)

	frappe.log_by_ajax(f"DEBUG: employee_query - Found {len(employee_list)} employees after filtering.")

	# Format the results as required by Link field get_query
	return [[employee.name, employee.employee_name] for employee in employee_list]
