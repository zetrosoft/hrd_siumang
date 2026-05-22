import frappe
from frappe import _

__version__ = '0.0.1'

def patch_report_globally():
    try:
        from frappe.core.doctype.report.report import Report
        
        if not hasattr(Report, 'original_execute_module'):
            Report.original_execute_module = Report.execute_module
            
            def custom_execute_module(self, filters):
                res = self.original_execute_module(filters)
                
                # Check if this is the target report
                if self.name == "Employee Exits" and isinstance(res, (list, tuple)) and len(res) >= 5:
                    # columns, data, message, chart, report_summary
                    res_list = list(res)
                    report_summary = res_list[4]
                    
                    if report_summary and isinstance(report_summary, list):
                        excluded_keywords = ["fnf", "questionnaire", "kuesioner"]
                        
                        new_summary = []
                        for item in report_summary:
                            label = str(item.get("label", "")).lower()
                            if not any(kw in label for kw in excluded_keywords):
                                new_summary.append(item)
                        
                        res_list[4] = new_summary
                    
                    return tuple(res_list)
                
                return res

            Report.execute_module = custom_execute_module
            # frappe.logger("patch").debug("Global Report execute_module patched for Employee Exits")
            
    except Exception:
        pass

# Initialize patches
patch_report_globally()
