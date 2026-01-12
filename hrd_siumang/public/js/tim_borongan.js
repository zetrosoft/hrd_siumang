frappe.ui.form.on("Tim Borongan", {
	refresh: function (frm) {
		frm.set_query("karyawan", "anggota_tim", function (doc, cdt, cdn) {
			return {
				filters: {
					employment_type: "Harian",
				},
				message: "Menampilkan karyawan dengan tipe 'Harian'",
			};
		});
	},
});
