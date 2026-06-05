// Copyright (c) 2026, Bijak Techno and contributors
// For license information, please see license.txt

frappe.ui.form.on("BPJS Setting", {
	refresh(frm) {
		frm.add_custom_button(__("Load Default Components"), () => {
			frm.call('load_defaults').then(r => {
				if (r.message) {
					frm.reload_doc();
				}
			});
		});
	},
});
