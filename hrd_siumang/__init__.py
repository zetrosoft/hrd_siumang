import frappe

__version__ = '0.0.1'

# Monkey Patch for Query Report API
def patch_query_report_run():
    try:
        from frappe.desk import query_report
        
        if not hasattr(query_report, 'original_run'):
            query_report.original_run = query_report.run
            
            @frappe.whitelist()
            def custom_run(report_name, filters=None, user=None, **kwargs):
                # Execute original run
                res = query_report.original_run(report_name, filters, user, **kwargs)
                
                # Check if it is the target report
                if report_name == "Employee Exits" and isinstance(res, dict) and "report_summary" in res:
                    summary = res.get("report_summary")
                    if summary and isinstance(summary, list):
                        # Force remove unwanted entries by label keywords
                        excluded_keywords = ["fnf", "questionnaire", "kuesioner"]
                        res["report_summary"] = [
                            i for i in summary 
                            if not any(kw in str(i.get("label", "")).lower() for kw in excluded_keywords)
                        ]
                return res

            # Override the whitelisted function
            query_report.run = custom_run
            
    except Exception:
        pass

# Initialize patches
patch_query_report_run()
