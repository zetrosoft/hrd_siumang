app_name = "hrd_siumang"
app_title = "Hrd Siumang"
app_publisher = "Bijak Techno"
app_description = "HRD Siumang Custom Apps"
app_email = "support@bijaktechnology.com"
app_license = "mit"

fixtures = [
	"payroll_fixtures.json",
	{"doctype": "Custom Field", "filters": [["module", "=", "hrd_siumang"]]},
	"overtime_planning_workflow.json",
	"overtime_planning_workflow_states.json",
	"hrd_siumang_custom_fields.json",
	"tarif_efektif_rata_rata.json",
]

doc_events = {
	"Job Requisition": {"before_save": "hrd_siumang.overrides.job_requisition_override.before_save"},
	"Overtime Planning": {"on_update": "hrd_siumang.doc_events.overtime_planning_events.on_update_or_submit"},
	"Salary Slip": {"before_save": "hrd_siumang.payroll.salary_slip_events.calculate_payroll_components"},
	"Salary Structure Assignment": {
		"before_save": "hrd_siumang.overrides.salary_structure_assignment.set_base_from_ctc"
	},
}
