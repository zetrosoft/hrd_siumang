/**
 * Employee Exits Report Customization
 * Metode Aman: Menggunakan CSS Hidden dan Re-render Interceptor
 */

frappe.query_reports["Employee Exits"] = $.extend(true, frappe.query_reports["Employee Exits"], {
    onload: function(report) {
        // Hapus filter dari konfigurasi sebelum dirender
        if (report.filters) {
            report.filters = report.filters.filter(f => 
                !['fnf_pending', 'questionnaire_pending', 'exit_interview_pending'].includes(f.fieldname)
            );
        }
    },
    after_render: function(report) {
        // Sembunyikan summary item secara visual (Aman dari error BaseChart.js)
        const hideSummary = () => {
            $(".report-summary .summary-item").each(function() {
                const label = $(this).find(".summary-label").text().toLowerCase();
                if (label.includes("fnf") || label.includes("questionnaire") || label.includes("kuesioner")) {
                    $(this).attr('style', 'display: none !important');
                }
            });
        };
        
        hideSummary();
        // Delay sedikit untuk mengantisipasi re-render chart
        setTimeout(hideSummary, 500);
    }
});

// Global CSS Injection sebagai pengaman terakhir
$(document).ready(function() {
    if (!$('#ee-custom-style').length) {
        $('head').append(`
            <style id="ee-custom-style">
                div[data-fieldname="fnf_pending"],
                div[data-fieldname="questionnaire_pending"],
                div[data-fieldname="exit_interview_pending"] {
                    display: none !important;
                }
            </style>
        `);
    }
});
