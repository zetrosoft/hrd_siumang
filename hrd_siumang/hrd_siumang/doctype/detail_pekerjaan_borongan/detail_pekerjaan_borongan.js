// Client script for Detail Pekerjaan Borongan (child table of Input Hasil Borongan)
frappe.ui.form.on("Detail Pekerjaan Borongan", {
	// This client script runs for each row in the child table.
	// 'frm' here refers to the main document form (Input Hasil Borongan),
	// 'cdt' and 'cdn' refer to the child doctype and child docname respectively.
	// 'row' refers to the current row object.

	pekerjaan_borongan: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (row.pekerjaan_borongan) {
			frappe.call({
				method: "hrd_siumang.hrd_siumang.doctype.detail_pekerjaan_borongan.detail_pekerjaan_borongan.get_job_setup_details_for_child",
				args: {
					job_name: row.pekerjaan_borongan,
				},
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "satuan", r.message.satuan);
						frappe.model.set_value(
							cdt,
							cdn,
							"harga_per_satuan",
							r.message.harga_per_satuan
						);
						frappe.model.set_value(cdt, cdn, "qty_hasil", 0); // Reset Qty on new selection

						// Call calculation function directly
						calculate_total_harga(frm, cdt, cdn);
					} else {
						frappe.model.set_value(cdt, cdn, "satuan", null);
						frappe.model.set_value(cdt, cdn, "harga_per_satuan", 0);
						frappe.model.set_value(cdt, cdn, "total_harga", 0);
					}
				},
			});
		}
	},

	qty_hasil: function (frm, cdt, cdn) {
		calculate_total_harga(frm, cdt, cdn);
	},

	harga_per_satuan: function (frm, cdt, cdn) {
		calculate_total_harga(frm, cdt, cdn);
	},
});

// Helper function for calculation, defined outside the main frappe.ui.form.on block
// so it can be called directly.
function calculate_total_harga(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const qty_hasil = flt(row.qty_hasil); // Use global flt
	const harga_per_satuan = flt(row.harga_per_satuan); // Use global flt
	frappe.model.set_value(cdt, cdn, "total_harga", qty_hasil * harga_per_satuan);
}
