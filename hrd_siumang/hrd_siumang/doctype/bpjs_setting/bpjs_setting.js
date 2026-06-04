// Copyright (c) 2026, Bijak Techno and contributors
// For license information, please see license.txt

frappe.ui.form.on("BPJS Setting", {
	refresh(frm) {
		frm.add_custom_button(__("Load Default Components"), () => {
			frappe.call({
				method: "hrd_siumang.hrd_siumang.doctype.bpjs_setting.bpjs_setting.load_defaults",
				callback: function(r) {
					frm.reload_doc();
				}
			});
		});
	},
});
