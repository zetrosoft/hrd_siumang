frappe.ui.form.on("Job Requisition", {
	refresh: function (frm) {
		// Hide the field from the form view
		frm.set_df_property("expected_compensation", "hidden", 1);

		// If the document is new and the value is not yet set,
		// set a default value to pass the 'mandatory' check upon saving.
		if (frm.is_new() && !frm.doc.expected_compensation) {
			frm.set_value("expected_compensation", 0);
		}
	},
});
