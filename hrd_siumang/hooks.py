app_name = "hrd_siumang"
app_title = "Hrd Siumang"
app_publisher = "Bijak Techno"
app_description = "HRD Siumang Custom Apps"
app_email = "support@bijaktechnology.com"
app_license = "mit"

override_whitelisted_methods = {
	"frappe.desk.query_report.run": "hrd_siumang.api.custom_query_report_run"
}

override_doctype_class = {
	"Job Requisition": "hrd_siumang.overrides.custom_job_requisition.CustomJobRequisition",
	"Salary Slip": "hrd_siumang.overrides.custom_salary_slip.CustomSalarySlip",
	"Payroll Entry": "hrd_siumang.overrides.custom_payroll_entry.CustomPayrollEntry",
}

app_include_js = [
	"/assets/hrd_siumang/js/employee_exits_custom.js",
	"/assets/hrd_siumang/js/hrms_overrides.js",
]

doctype_js = {
	"Job Requisition": "public/js/job_requisition_workflow.js",
	"Overtime Planning": "hrd_siumang/doctype/overtime_planning/overtime_planning.js",
	"Input Hasil Borongan": "public/js/input_hasil_borongan.js",
	"Tim Borongan": "public/js/tim_borongan.js",
	"Employee Advance": "public/js/employee_advance_client.js",
}

doc_events = {
	"Salary Slip": {
		"before_save": "hrd_siumang.payroll.salary_slip_events.calculate_payroll_components"
	},
	"Salary Structure Assignment": {
		"before_save": "hrd_siumang.overrides.salary_structure_assignment.set_base_from_ctc"
	}
}
