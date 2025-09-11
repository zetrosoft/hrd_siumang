frappe.ui.form.on("Job Requisition", {
	refresh: function (frm) {
		// Set value to 0, make non-mandatory, then hide "Expected Compensation"
		frm.set_value("expected_compensation", 0);
		frm.toggle_reqd("expected_compensation", false);
		frm.toggle_display("expected_compensation", false);
	},
});
