frappe.ui.form.on('Deduction Salary', {
    setup: function(frm) {
        // Filter Salary Component dropdown to ONLY show Deductions
        frm.set_query("salary_component", function() {
            return {
                filters: {
                    type: "Deduction"
                }
            };
        });
    },
    
    employee: function(frm) {
        // Clear components if employee changes
        if (frm.doc.employee) {
            frappe.run_serially([
                () => frappe.db.get_value('Employee', frm.doc.employee, 'company', (r) => {
                    if (r && r.company) {
                        frm.set_value('company', r.company);
                    }
                })
            ]);
        }
    }
});