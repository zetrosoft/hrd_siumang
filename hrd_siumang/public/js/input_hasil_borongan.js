// Client Script for Input Hasil Borongan (Main DocType)
console.log("Input Hasil Borongan client script loaded!");

frappe.ui.form.on("Input Hasil Borongan", {
	refresh: function (frm) {
		console.log("DEBUG: Event 'refresh' fired.");
		frm.call("calculate_summary_totals");

		console.log("DEBUG: Setting up 'karyawan' query on parent refresh.");
		frm.set_query("karyawan", "detail_hasil_borongan_table", function (doc, cdt, cdn) {
			//console.log("DEBUG: Main query function is executing for a row.");
			let d = locals[cdt][cdn];
			if (d.tipe_penerima_tugas === "Individu") {
				return {
					query: "hrd_siumang.hrd_siumang.doctype.detail_hasil_borongan.detail_hasil_borongan.get_harian_employees",
				};
			}
			return {};
		});
	},

	pekerjaan_borongan: function (frm) {
		console.log("DEBUG: Event 'pekerjaan_borongan' fired. Value:", frm.doc.pekerjaan_borongan);
		if (frm.doc.pekerjaan_borongan) {
			frappe.call({
				method: "hrd_siumang.hrd_siumang.doctype.input_hasil_borongan.input_hasil_borongan.get_pekerjaan_details",
				args: { pekerjaan_borongan_name: frm.doc.pekerjaan_borongan },
				callback: function (r) {
					console.log("DEBUG: Callback for 'get_pekerjaan_details' executed.");
					if (r.message && r.message.harga_per_satuan) {
						frm.set_value("harga_per_satuan", r.message.harga_per_satuan);
						frm.set_value("satuan", r.message.satuan);

						console.log(
							"DEBUG: Updating child table rows with price:",
							r.message.harga_per_satuan
						);
						(frm.doc.detail_hasil_borongan_table || []).forEach(function (row) {
							row.harga_item = r.message.harga_per_satuan;
						});
						frm.refresh_field("detail_hasil_borongan_table");
					} else {
						console.log("DEBUG: No message received from 'get_pekerjaan_details'.");
						frm.set_value("harga_per_satuan", 0);
						frm.set_value("satuan", null);
					}
				},
			});
		} else {
			console.log("DEBUG: 'pekerjaan_borongan' cleared.");
			frm.set_value("harga_per_satuan", 0);
			frm.set_value("satuan", null);
		}
	},
});

// Listener for changes in child table to update parent totals
frappe.ui.form.on("Detail Hasil Borongan", {
	jumlah_dihasilkan: function (frm) {
		console.log("DEBUG: Event 'jumlah_dihasilkan' in child table fired.");
		frm.call("calculate_summary_totals");
	},
	harga_item: function (frm) {
		console.log("DEBUG: Event 'harga_item' in child table fired.");
		frm.call("calculate_summary_totals");
	},
	detail_hasil_borongan_table_remove: function (frm) {
		//console.log("DEBUG: Event 'detail_hasil_borongan_table_remove' fired.");
		frm.call("calculate_summary_totals");
	},
});
