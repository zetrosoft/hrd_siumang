$(document).on('ajaxComplete', function(event, xhr, settings) {
    if (settings.url && settings.url.indexOf('method=frappe.desk.query_report.run') !== -1) {
        // Cek apakah ini report Employee Exits
        if (settings.data && settings.data.indexOf('report_name=Employee%20Exits') !== -1) {
            setTimeout(() => {
                $(".report-summary .summary-item").each(function() {
                    let label = $(this).find(".summary-label").text().trim();
                    if (label === __("Pending FnF") || label === __("Pending Questionnaires")) {
                        $(this).css("display", "none");
                    }
                });
            }, 500); // Memberikan jeda agar render Frappe selesai
        }
    }
});
