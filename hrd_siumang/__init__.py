import frappe
from frappe import _

__version__ = '0.0.1'

# Monkey Patch for Employee Exits Report
def patch_employee_exits_summary():
    try:
        from hrms.hr.report.employee_exits import employee_exits
        
        # Simpan fungsi aslinya
        if not hasattr(employee_exits, 'original_get_report_summary'):
            employee_exits.original_get_report_summary = employee_exits.get_report_summary
            
            def custom_get_report_summary(data):
                # Panggil fungsi asli untuk dapat data awal
                summary = employee_exits.original_get_report_summary(data)
                
                if summary:
                    # Filter: Hanya simpan yang labelnya BUKAN Pending FnF atau Pending Questionnaires
                    # Gunakan _() agar mencocokkan label yang sudah diterjemahkan maupun aslinya
                    excluded_labels = [
                        _("Pending FnF"), 
                        _("Pending Questionnaires"),
                        "Pending FnF", 
                        "Pending Questionnaires"
                    ]
                    
                    filtered_summary = []
                    for item in summary:
                        label = item.get("label")
                        if label not in excluded_labels:
                            filtered_summary.append(item)
                    
                    return filtered_summary
                return summary

            # Timpa fungsi asli dengan fungsi kustom kita
            employee_exits.get_report_summary = custom_get_report_summary
            
    except ImportError:
        # Jika hrms belum terinstall atau path berubah, jangan gagalkan startup
        pass

# Jalankan patch saat aplikasi dimuat
patch_employee_exits_summary()
