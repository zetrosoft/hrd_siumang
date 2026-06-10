# Copyright (c) 2026, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Job Title"),
			"fieldname": "job_title",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 150
		},
		{
			"label": _("Total Applicants"),
			"fieldname": "total_applicants",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("Interviewed"),
			"fieldname": "interviewed",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Cleared"),
			"fieldname": "cleared",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Rejected"),
			"fieldname": "rejected",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Hired"),
			"fieldname": "hired",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Conversion Rate (%)"),
			"fieldname": "conversion_rate",
			"fieldtype": "Percent",
			"width": 140
		}
	]

def get_data(filters):
	data = []
	
	# Get all Job Openings for the company
	openings = frappe.get_all("Job Opening", filters={"company": filters.get("company")}, fields=["name", "job_title", "designation"])
	
	for opening in openings:
		# Total Applicants for this opening
		applicant_filters = {"job_title": opening.name}
		if filters.get("from_date") and filters.get("to_date"):
			applicant_filters["creation"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		
		total_applicants = frappe.db.count("Job Applicant", applicant_filters)
		
		# Interviewed (Unique applicants who have an Interview record)
		interviewed = frappe.db.sql("""
			SELECT COUNT(DISTINCT job_applicant) 
			FROM `tabInterview` 
			WHERE job_opening = %s
		""", (opening.name,))[0][0] or 0
		
		# Cleared (Applicants who have at least one 'Cleared' Interview)
		cleared = frappe.db.sql("""
			SELECT COUNT(DISTINCT job_applicant) 
			FROM `tabInterview` 
			WHERE job_opening = %s AND status = 'Cleared'
		""", (opening.name,))[0][0] or 0
		
		# Rejected (Job Applicants with status 'Rejected')
		rejected_filters = applicant_filters.copy()
		rejected_filters["status"] = "Rejected"
		rejected = frappe.db.count("Job Applicant", rejected_filters)
		
		# Hired (Job Applicants with status 'Accepted')
		hired_filters = applicant_filters.copy()
		hired_filters["status"] = "Accepted"
		hired = frappe.db.count("Job Applicant", hired_filters)
		
		conversion_rate = (hired / total_applicants * 100) if total_applicants > 0 else 0
		
		data.append({
			"job_title": opening.job_title,
			"designation": opening.designation,
			"total_applicants": total_applicants,
			"interviewed": interviewed,
			"cleared": cleared,
			"rejected": rejected,
			"hired": hired,
			"conversion_rate": conversion_rate
		})
		
	return data
