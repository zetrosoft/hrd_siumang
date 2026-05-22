/**
 * Employee Exits Customization
 * Menyembunyikan statistik dan filter menggunakan CSS (Safe Method)
 */
$(document).on('app_ready', function() {
    const style = document.createElement('style');
    style.innerHTML = `
        /* Sembunyikan summary item berdasarkan urutan atau teks jika memungkinkan */
        /* Karena kita mem-patch server, item ini seharusnya sudah hilang dari JSON */
        /* CSS ini sebagai pengaman tambahan */
        .report-summary .summary-item:nth-child(3), 
        .report-summary .summary-item:nth-child(4) {
            display: none !important;
        }

        /* Sembunyikan Filter Dashboard */
        div[data-fieldname="fnf_pending"],
        div[data-fieldname="questionnaire_pending"],
        div[data-fieldname="exit_interview_pending"] {
            display: none !important;
        }
    `;
    document.head.appendChild(style);
});

// Tetap gunakan logic JS untuk membersihkan objek filter jika dimungkinkan
frappe.query_reports["Employee Exits"] = $.extend(true, frappe.query_reports["Employee Exits"], {
    onload: function(report) {
        if (report.filters) {
            report.filters = report.filters.filter(f => 
                !['fnf_pending', 'questionnaire_pending', 'exit_interview_pending'].includes(f.fieldname)
            );
        }
    }
});
