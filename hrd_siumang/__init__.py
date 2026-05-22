import frappe
from frappe import _

__version__ = '0.0.1'

# Monkey Patch for Employee Exits Report
def patch_employee_exits_report():
    try:
        from hrms.hr.report.employee_exits import employee_exits
        
        # Patch the main execute function for total control
        if not hasattr(employee_exits, 'original_execute'):
            employee_exits.original_execute = employee_exits.execute
            
            def custom_execute(filters=None):
                # Run the original report logic
                result = employee_exits.original_execute(filters)
                
                # result is expected to be: columns, data, message, chart, report_summary
                if result and len(result) >= 5:
                    columns, data, message, chart, report_summary = list(result)
                    
                    if report_summary:
                        # Defensive filtering
                        excluded_keywords = [
                            "pending fnf", 
                            "pending questionnaires", 
                            "fnf tertunda", 
                            "kuesioner tertunda"
                        ]
                        
                        new_summary = []
                        for item in report_summary:
                            label = str(item.get("label", "")).lower()
                            # Check if any keyword matches the label
                            if not any(kw in label for kw in excluded_keywords):
                                new_summary.append(item)
                        
                        report_summary = new_summary
                    
                    return columns, data, message, chart, report_summary
                
                return result

            # Override the module function
            employee_exits.execute = custom_execute
            
    except Exception:
        pass

# Run the patch
patch_employee_exits_report()
