frappe.ui.form.on("Overtime Planning", {
	// Event ini berjalan saat form dimuat atau di-refresh
	refresh: function (frm) {
		// Atur kueri untuk field 'employee' di dalam tabel 'overtime_details'
		frm.set_query("employee", "overtime_details", function (doc, cdt, cdn) {
			// 'doc' di sini adalah dokumen induk 'Overtime Planning'
			if (!doc.department) {
				frappe.throw(__("Silakan pilih Departemen terlebih dahulu."));
				return {};
			}
			return {
				filters: {
					department: doc.department,
				},
			};
		});

		// Set departemen default berdasarkan departemen karyawan user yang login
		if (!frm.doc.department && frappe.session.user !== "Administrator") {
			frappe.db.get_value(
				"Employee",
				{ user_id: frappe.session.user },
				"department",
				(r) => {
					if (r && r.department) {
						frm.set_value("department", r.department);
					}
				}
			);
		}
	},

	// Event ini berjalan saat field 'department' diubah
	department: function (frm) {
		// Jika departemen dipilih, kosongkan tabel anak karena
		// entri karyawan yang lama mungkin tidak valid lagi.
		if (frm.doc.department) {
			frm.set_value("overtime_details", []);
		}
		// Refresh field tabel untuk menampilkannya sebagai kosong
		frm.refresh_field("overtime_details");
	},
});
