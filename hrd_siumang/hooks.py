app_name = "hrd_siumang"
app_title = "Hrd Siumang"
app_publisher = "Bijak Techno"
app_description = "HRD Siumang Custom Apps"
app_email = "support@bijaktechnology.com"
app_license = "mit"

fixtures = [
	"payroll_fixtures.json",
	{"doctype": "Custom Field", "filters": [["module", "=", "hrd_siumang"]]},
	"overtime_planning_workflow.json",  # Fixture baru
	"overtime_planning_workflow_states.json",  # Fixture baru
	"hrd_siumang_custom_fields.json",  # Fixture custom field baru
	# {"doctype": "Tarif Efektif Rerata", "file": "tarif_efektif_rerata.json", "overwrite": True} # Fixture TER baru
]

# ... (bagian app_include_css, app_include_js, dll. tetap sama) ...

doctype_js = {
	"Job Requisition": "hrd_siumang/public/js/job_requisition_client_script.js",
	"Overtime Planning": "hrd_siumang/hrd_siumang/doctype/overtime_planning/overtime_planning.js",
}
doctype_list_js = {
	"Overtime Planning": "hrd_siumang/public/js/overtime_planning_list.js"  # JS baru
}
# ... (bagian lainnya tetap sama) ...

doc_events = {
	"Job Requisition": {"before_save": "hrd_siumang.overrides.job_requisition_override.before_save"},
	"Overtime Planning": {
		"on_update": "hrd_siumang.doc_events.overtime_planning_events.on_update_or_submit"
	},  # Hook lama
	"Salary Slip": {
		"before_save": "hrd_siumang.payroll.salary_slip_events.calculate_payroll_components"
	},  # Hook baru
	"Salary Structure Assignment": {
		"before_save": "hrd_siumang.overrides.salary_structure_assignment.set_base_from_ctc"
	},  # Hook untuk otomatisasi CTC
}
