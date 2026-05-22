// Employee Exits Report UI Customization
frappe.query_reports["Employee Exits"] = $.extend(true, frappe.query_reports["Employee Exits"], {
    onload: function(report) {
        // Hapus filter yang tidak diinginkan dari definisi laporan
        if (report.report_name === "Employee Exits" && report.filters) {
            const excluded_fields = ['fnf_pending', 'questionnaire_pending', 'exit_interview_pending'];
            report.filters = report.filters.filter(f => !excluded_fields.includes(f.fieldname));
        }
    },
    after_render: function(report) {
        // Sembunyikan elemen statistik yang mengandung kata kunci FnF atau Questionnaire
        $(".report-summary .summary-item").each(function() {
            let label = $(this).find(".summary-label").text().toLowerCase();
            if (label.includes("fnf") || label.includes("questionnaire") || label.includes("kuesioner")) {
                $(this).hide();
            }
        });
    }
});
