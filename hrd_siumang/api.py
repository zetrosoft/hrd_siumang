import frappe
from frappe.desk.query_report import run as original_run

@frappe.whitelist()
def custom_query_report_run(report_name, filters=None, user=None, **kwargs):
    # Paksa hapus cache untuk laporan ini jika ada
    if report_name == "Employee Exits":
        frappe.cache.delete_value(f"report_result:Employee Exits:{frappe.session.user}")
        
    res = original_run(report_name, filters, user, **kwargs)
    
    if report_name == "Employee Exits" and isinstance(res, dict) and "report_summary" in res:
        summary = res.get("report_summary")
        if summary:
            # Filter berdasarkan label secara case-insensitive
            excluded = ["fnf", "questionnaire", "kuesioner"]
            new_summary = [
                i for i in summary 
                if not any(kw in str(i.get("label", "")).lower() for kw in excluded)
            ]
            res["report_summary"] = new_summary
            
            # Log Bukti ke Error Log
            frappe.log_error(f"Summary terfilter: {len(new_summary)} item", "PATCH_EE_SUCCESS")
            
    return res
