// Client Script for Input Hasil Borongan (Main DocType)

// --- PARENT DOCTYPE EVENTS ---
frappe.ui.form.on("Input Hasil Borongan", {
	refresh: function (frm) {
		frm.call("calculate_summary_totals");

		frm.set_query("karyawan", "detail_hasil_borongan_table", function (doc, cdt, cdn) {
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
		if (frm.doc.pekerjaan_borongan) {
			frappe.call({
				method: "hrd_siumang.hrd_siumang.doctype.input_hasil_borongan.input_hasil_borongan.get_pekerjaan_details",
				args: { pekerjaan_borongan_name: frm.doc.pekerjaan_borongan },
				callback: function (r) {
					if (r.message && r.message.harga_per_satuan) {
						frm.set_value("harga_per_satuan", r.message.harga_per_satuan);
						frm.set_value("satuan", r.message.satuan);

						(frm.doc.detail_hasil_borongan_table || []).forEach(function (row) {
							row.harga_item = r.message.harga_per_satuan;
						});
						frm.refresh_field("detail_hasil_borongan_table");
					} else {
						frm.set_value("harga_per_satuan", 0);
						frm.set_value("satuan", null);
					}
				},
			});
		} else {
			frm.set_value("harga_per_satuan", 0);
			frm.set_value("satuan", null);
		}
	},
});

// --- CHILD DOCTYPE EVENTS ---
frappe.ui.form.on("Detail Hasil Borongan", {
	karyawan: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if ((!row.harga_item || row.harga_item === 0) && frm.doc.harga_per_satuan > 0) {
			frappe.model.set_value(cdt, cdn, "harga_item", frm.doc.harga_per_satuan);
		}
	},

	tipe_penerima_tugas: function (frm, cdt, cdn) {
		let link_doctype_value = null;
		let row = frappe.get_doc(cdt, cdn);

		if (row.tipe_penerima_tugas === "Individu") {
			link_doctype_value = "Employee";
		} else if (row.tipe_penerima_tugas === "Tim") {
			link_doctype_value = "Tim Borongan";
		}

		frappe.model.set_value(cdt, cdn, "link_doctype", link_doctype_value);
		frappe.model.set_value(cdt, cdn, "karyawan", null);

		frm.get_field("detail_hasil_borongan_table")
			.grid.grid_rows_by_docname[cdn].get_field("karyawan")
			.refresh();
	},

	jumlah_dihasilkan: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		let total = flt(row.jumlah_dihasilkan) * flt(row.harga_item);
		frappe.model.set_value(cdt, cdn, "total_harga_item", total);
		frm.call("calculate_summary_totals");
	},

	harga_item: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		let total = flt(row.jumlah_dihasilkan) * flt(row.harga_item);
		frappe.model.set_value(cdt, cdn, "total_harga_item", total);
		frm.call("calculate_summary_totals");
	},

	detail_hasil_borongan_table_remove: function (frm) {
		frm.call("calculate_summary_totals");
	},
});
