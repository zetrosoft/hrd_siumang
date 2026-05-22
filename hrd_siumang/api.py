import frappe
from frappe.desk.query_report import run as original_run

@frappe.whitelist()
def custom_query_report_run(report_name, filters=None, user=None, **kwargs):
    # Log ke Error Log agar Anda bisa memverifikasi di Desk
    frappe.log_error(f"API Patch Terpanggil untuk: {report_name}", "DEBUG_PATCH_EE")
    
    # Jalankan fungsi asli
    res = original_run(report_name, filters, user, **kwargs)
    
    # Intersepsi hasil khusus untuk Employee Exits
    if report_name == "Employee Exits" and isinstance(res, dict) and "report_summary" in res:
        summary = res.get("report_summary")
        if summary:
            excluded = ["fnf", "questionnaire", "kuesioner"]
            new_summary = [
                i for i in summary 
                if not any(kw in str(i.get("label", "")).lower() for kw in excluded)
            ]
            res["report_summary"] = new_summary
            frappe.log_error(f"Summary Berhasil Difilter: {len(new_summary)} item tersisa", "DEBUG_PATCH_EE")
            
    return res
