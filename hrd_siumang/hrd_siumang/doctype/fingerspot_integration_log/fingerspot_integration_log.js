// Copyright (c) 2025, Bijak Techno and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fingerspot Integration Log", {
	refresh: function (frm) {
		frm.clear_custom_buttons();
		frm.add_custom_button(__("Sync Now"), function () {
			frm.call("sync_fingerspot_data", {
				start_date: frm.doc.last_sync_datetime
					? moment(frm.doc.last_sync_datetime).format("YYYY-MM-DD")
					: undefined,
				end_date: moment().format("YYYY-MM-DD"),
			}).then((r) => {
				if (r.message) {
					frappe.show_alert({
						message: __("Fingerspot sync initiated."),
						indicator: "green",
					});
					frm.reload_doc();
				}
			});
		}).addClass("btn-primary");
	},

	sync_frequency: function (frm) {
		frm.toggle_display("specific_sync_times", frm.doc.sync_frequency == "Specific Times");
	},
});
