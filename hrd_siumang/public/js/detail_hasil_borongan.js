// Client Script for Detail Hasil Borongan (Child Table)
console.log("Detail Hasil Borongan client script loaded!");

frappe.ui.form.on("Detail Hasil Borongan", {
	// Trigger to set default price as a workaround for _add event not firing
	karyawan: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if ((!row.harga_item || row.harga_item === 0) && frm.doc.harga_per_satuan > 0) {
			console.log("DEBUG: 'karyawan' changed, setting default 'harga_item'.");
			frappe.model.set_value(cdt, cdn, "harga_item", frm.doc.harga_per_satuan);
		}
	},

	// Main logic for switching the Dynamic Link
	tipe_penerima_tugas: function (frm, cdt, cdn) {
		console.log("DEBUG: 'tipe_penerima_tugas' changed.");

		let link_doctype_value = null;
		let row = frappe.get_doc(cdt, cdn);

		if (row.tipe_penerima_tugas === "Individu") {
			link_doctype_value = "Employee";
		} else if (row.tipe_penerima_tugas === "Tim") {
			link_doctype_value = "Tim Borongan";
		}

		// Set the hidden 'link_doctype' field, which controls the Dynamic Link
		frappe.model.set_value(cdt, cdn, "link_doctype", link_doctype_value);
		console.log("DEBUG: Hidden field 'link_doctype' set to:", link_doctype_value);

		// Clear the 'karyawan' field since its type has changed
		frappe.model.set_value(cdt, cdn, "karyawan", null);

		// Refresh the 'karyawan' field to apply the new link type
		frm.get_field("detail_hasil_borongan_table")
			.grid.grid_rows_by_docname[cdn].get_field("karyawan")
			.refresh();
	},

	// Calculation triggers
	jumlah_dihasilkan: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		let total = flt(row.jumlah_dihasilkan) * flt(row.harga_item);
		frappe.model.set_value(cdt, cdn, "total_harga_item", total);
	},

	harga_item: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		let total = flt(row.jumlah_dihasilkan) * flt(row.harga_item);
		frappe.model.set_value(cdt, cdn, "total_harga_item", total);
	},
});
