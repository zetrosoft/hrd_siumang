app_name = "hrd_siumang"
app_title = "Hrd Siumang"
app_publisher = "Bijak Techno"
app_description = "HRD Siumang Custom Apps"
app_email = "support@bijaktechnology.com"
app_license = "mit"

override_doctype_class = {
	"Job Requisition": "hrd_siumang.overrides.custom_job_requisition.CustomJobRequisition",
	"Salary Slip": "hrd_siumang.overrides.custom_salary_slip.CustomSalarySlip",
	"Payroll Entry": "hrd_siumang.overrides.custom_payroll_entry.CustomPayrollEntry",
}

fixtures = [
	"job_requisition_approval.json",
	"job_requisition_workflow_states.json",
	"job_requisition_approval_history_visible.json",
	"payroll_fixtures.json",
	{"doctype": "Custom Field", "filters": [["module", "=", "hrd_siumang"]]},
	"overtime_planning_workflow.json",  # Fixture baru
	"overtime_planning_workflow_states.json",  # Fixture baru
	"hrd_siumang_custom_fields.json",  # Fixture custom field baru
	{
		"doctype": "Tarif Efektif Rerata",
		"file": "tarif_efektif_rerata.json",
		"overwrite": True,
	},  # Fixture TER baru
	"Fingerspot Integration Log",  # Fixture baru
	"Setup Pekerjaan Borongan",
	"Tim Borongan",
	"Anggota Tim Borongan",  # Child Table
	"Penugasan Borongan",
	"employee_advance_workflow.json",
	"employee_advance_custom_fields.json",
]

doctype_js = {
	"Job Requisition": "public/js/job_requisition_workflow.js",
	"Overtime Planning": "hrd_siumang/doctype/overtime_planning/overtime_planning.js",
	"Payroll Validation Process": "hrd_siumang/doctype/payroll_validation_process/payroll_validation_process.js",
	"Validasi Kesiapan Payroll": "hrd_siumang/doctype/validasi_kesiapan_payroll/validasi_kesiapan_payroll.js",
	"Fingerspot Integration Log": "hrd_siumang/doctype/fingerspot_integration_log/fingerspot_integration_log.js",
	"Input Hasil Borongan": "public/js/input_hasil_borongan.js",
	"Tim Borongan": "public/js/tim_borongan.js",
	"Employee Advance": "public/js/employee_advance_client.js",
}
doctype_list_js = {"Overtime Planning": "public/js/overtime_planning_list.js"}

doc_events = {
	"Job Requisition": {"on_update": "hrd_siumang.doc_events.job_requisition_events.on_update"},
	"Overtime Planning": {"on_update": "hrd_siumang.doc_events.overtime_planning_events.on_update_or_submit"},
	"Employee Advance": {
		"on_update": "hrd_siumang.doc_events.employee_advance_events.send_notification_on_state_change"
	},
	"Salary Slip": {"before_save": "hrd_siumang.payroll.salary_slip_events.calculate_payroll_components"},
	"Salary Structure Assignment": {
		"before_save": "hrd_siumang.overrides.salary_structure_assignment.set_base_from_ctc"
	},
}

# scheduler_events = {
# 	"all": [
# 		"hrd_siumang.doctype.fingerspot_integration_log.fingerspot_integration_log.run_fingerspot_sync_from_scheduler"
# 	]
# }

# patches = ["hrd_siumang.patches.20260110_add_borongan_management_card_to_payroll.execute"]

# javascript files to be included in header of desk.html
# app_include_js = [
# 	"/assets/hrd_siumang/js/input_hasil_borongan.js",
# 	"/assets/hrd_siumang/js/detail_hasil_borongan.js",
# ]
