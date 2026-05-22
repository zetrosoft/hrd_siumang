import frappe
from frappe import _

__version__ = '0.0.1'

# Monkey Patch for Employee Exits Report
def patch_employee_exits_summary():
    try:
        from hrms.hr.report.employee_exits import employee_exits
        
        # Simpan fungsi aslinya jika belum ada
        if not hasattr(employee_exits, 'original_get_report_summary'):
            employee_exits.original_get_report_summary = employee_exits.get_report_summary
            
            def custom_get_report_summary(data):
                # Panggil fungsi asli
                summary = employee_exits.original_get_report_summary(data)
                
                if not summary:
                    return summary
                
                # List label yang ingin dibuang (dalam berbagai kemungkinan bahasa)
                # Gunakan set untuk pencarian lebih cepat dan robust
                to_exclude = {
                    _("Pending FnF").strip(),
                    _("Pending Questionnaires").strip(),
                    "Pending FnF",
                    "Pending Questionnaires",
                    "FnF Tertunda", # Manual check Bahasa Indonesia
                    "Kuesioner Tertunda"
                }
                
                filtered_summary = []
                for item in summary:
                    label = str(item.get("label", "")).strip()
                    # Log untuk debugging (cek di logs/frappe.log atau logs/worker.log)
                    # frappe.logger("patch").debug(f"Checking label: {label}")
                    
                    if label not in to_exclude:
                        filtered_summary.append(item)
                
                return filtered_summary

            # Timpa fungsi asli
            employee_exits.get_report_summary = custom_get_report_summary
            # frappe.logger("patch").debug("Employee Exits Report summary patched successfully")
            
    except Exception as e:
        # frappe.logger("patch").error(f"Failed to patch Employee Exits Report: {e}")
        pass

# Jalankan patch
patch_employee_exits_summary()
