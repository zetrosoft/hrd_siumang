/**
 * Definitively hide statistics and filters for Employee Exits report.
 * Uses Object.defineProperty to intercept report definition and prevents overwriting.
 */
(function() {
    if (window.frappe && !window.frappe._ee_patched) {
        
        const target_report = "Employee Exits";
        const excluded_fields = ['fnf_pending', 'questionnaire_pending', 'exit_interview_pending'];

        // Intercept frappe.query_reports
        let _query_reports = frappe.query_reports || {};
        
        Object.defineProperty(frappe, 'query_reports', {
            get: function() { return _query_reports; },
            set: function(val) {
                _query_reports = val;
                setupReportInterceptor();
            },
            configurable: true
        });

        function setupReportInterceptor() {
            let _ee_config = _query_reports[target_report];

            Object.defineProperty(_query_reports, target_report, {
                get: function() { return _ee_config; },
                set: function(new_config) {
                    if (new_config && new_config.filters) {
                        // Filter out unwanted fields immediately
                        new_config.filters = new_config.filters.filter(f => !excluded_fields.includes(f.fieldname));
                    }
                    _ee_config = new_config;
                },
                configurable: true
            });
        }

        // Run initially if already exists
        setupReportInterceptor();
        
        window.frappe._ee_patched = true;
    }
})();
