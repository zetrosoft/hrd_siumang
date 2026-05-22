import frappe

# DEBUG: Bukti bahwa hooks dimuat. Cek Error Log setelah restart.
try:
    frappe.log_error("Aplikasi hrd_siumang Hooks Dimuat", "HOOK_LOADED")
except:
    pass

app_name = "hrd_siumang"
app_title = "Hrd Siumang"
app_publisher = "Bijak Techno"
app_description = "HRD Siumang Custom Apps"
app_email = "support@bijaktechnology.com"
app_license = "mit"

# MONKEY PATCH DEFINITIF
import frappe.desk.query_report as query_report
if not hasattr(query_report, 'original_run'):
    query_report.original_run = query_report.run
    
    def custom_run(report_name, filters=None, user=None, **kwargs):
        res = query_report.original_run(report_name, filters, user, **kwargs)
        if report_name == "Employee Exits" and isinstance(res, dict) and "report_summary" in res:
            # Saring summary secara agresif
            res["report_summary"] = [
                i for i in res["report_summary"] 
                if not any(kw in str(i.get("label", "")).lower() for kw in ["fnf", "questionnaire", "kuesioner"])
            ]
            frappe.log_error("Patch Berhasil Memfilter Laporan Employee Exits", "DEBUG_PATCH_EE")
        return res
    
    query_report.run = custom_run

# Konfigurasi Hooks Standar
override_doctype_class = {
	"Job Requisition": "hrd_siumang.overrides.custom_job_requisition.CustomJobRequisition",
	"Salary Slip": "hrd_siumang.overrides.custom_salary_slip.CustomSalarySlip",
	"Payroll Entry": "hrd_siumang.overrides.custom_payroll_entry.CustomPayrollEntry",
}

app_include_js = [
	"/assets/hrd_siumang/js/employee_exits_custom.js",
]

doctype_js = {
	"Job Requisition": "public/js/job_requisition_workflow.js",
	"Overtime Planning": "hrd_siumang/doctype/overtime_planning/overtime_planning.js",
	"Input Hasil Borongan": "public/js/input_hasil_borongan.js",
	"Tim Borongan": "public/js/tim_borongan.js",
	"Employee Advance": "public/js/employee_advance_client.js",
}
