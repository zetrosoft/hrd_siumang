// Customization for Employee Exits Report
frappe.query_report_callbacks = frappe.query_report_callbacks || {};

$(document).on('ajaxComplete', function(event, xhr, settings) {
    if (settings.url && settings.url.indexOf('method=frappe.desk.query_report.run') !== -1) {
        if (settings.data && settings.data.indexOf('report_name=Employee%20Exits') !== -1) {
            
            // 1. Hide Statistics (Summary)
            setTimeout(() => {
                $(".report-summary .summary-item").each(function() {
                    let label = $(this).find(".summary-label").text().toLowerCase();
                    if (label.includes("fnf") || label.includes("questionnaire") || label.includes("kuesioner")) {
                        $(this).remove(); // Gunakan remove agar layout merapat
                    }
                });
                
                // 2. Hide Filters
                // Mencari filter berdasarkan fieldname atau label
                if (cur_report && cur_report.filters_fields_dict) {
                    const to_hide = ['fnf_pending', 'questionnaire_pending'];
                    to_hide.forEach(fieldname => {
                        let field = cur_report.filters_fields_dict[fieldname];
                        if (field) {
                            field.wrapper.hide();
                        }
                    });
                }
            }, 500);
        }
    }
});
