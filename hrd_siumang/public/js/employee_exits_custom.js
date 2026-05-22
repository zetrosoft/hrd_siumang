// Customization for Employee Exits Report
$(document).on('ajaxComplete', function(event, xhr, settings) {
    if (settings.url && settings.url.indexOf('method=frappe.desk.query_report.run') !== -1) {
        if (settings.data && settings.data.indexOf('report_name=Employee%20Exits') !== -1) {
            
            // Function to perform hiding
            const hideTargetElements = () => {
                // 1. Hide Statistics (Summary)
                $(".report-summary .summary-item").each(function() {
                    let label = $(this).find(".summary-label").text().toLowerCase();
                    if (label.includes("fnf") || label.includes("questionnaire") || label.includes("kuesioner")) {
                        $(this).hide();
                    }
                });
                
                // 2. Hide Filters from the filter dashboard
                if (window.cur_report && cur_report.filters_fields_dict) {
                    const to_hide = ['fnf_pending', 'questionnaire_pending', 'exit_interview_pending'];
                    to_hide.forEach(fieldname => {
                        let field = cur_report.filters_fields_dict[fieldname];
                        if (field && field.wrapper) {
                            $(field.wrapper).hide();
                        }
                    });
                }
                
                // 3. Fallback: hide by label text in filters
                $(".frappe-control[data-fieldname]").each(function() {
                    let fieldname = $(this).attr("data-fieldname");
                    if (fieldname && (fieldname.includes("fnf") || fieldname.includes("questionnaire") || fieldname.includes("interview_pending"))) {
                        $(this).hide();
                    }
                });
            };

            // Run multiple times to catch Frappe's re-renders
            hideTargetElements();
            setTimeout(hideTargetElements, 500);
            setTimeout(hideTargetElements, 1500);
            setTimeout(hideTargetElements, 3000);
        }
    }
});
