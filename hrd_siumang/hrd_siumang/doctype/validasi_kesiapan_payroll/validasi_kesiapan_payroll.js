frappe.ui.form.on("Validasi Kesiapan Payroll", {
	refresh: function (frm) {
		frm.clear_custom_buttons(); // Clear all old buttons

		// Add the new unified button
		frm.add_custom_button(
			__("Prepare Payroll Attendance Data"),
			function () {
				handle_process_start(
					frm,
					"enqueue_prepare_payroll_data", // New unified enqueue method
					"payroll_attendance_summary_link" // Result field (HTML link)
				);
			},
			__("Actions")
		).attr("id", "btn-prepare-payroll-data"); // Add an ID for easier manipulation

		// Initial state update for the button
		update_prepare_button_state(frm);
	},

	// Handle changes to the period selection
	payroll_period_link: function (frm) {
		update_prepare_button_state(frm);
	},

	// Handle changes to each checklist item
	checklist_master_active_employees: function (frm) {
		update_prepare_button_state(frm);
	},
	checklist_company_holiday_list: function (frm) {
		update_prepare_button_state(frm);
	},
	checklist_daily_attendance_data: function (frm) {
		update_prepare_button_state(frm);
	},
	checklist_approved_leave_applications: function (frm) {
		update_prepare_button_state(frm);
	},
	checklist_perencanaan_lembur_disetujui: function (frm) {
		update_prepare_button_state(frm);
	},
	checklist_konfigurasi_hr_settings: function (frm) {
		update_prepare_button_state(frm);
	},
});

function update_prepare_button_state(frm) {
	const prepareButton = $("#btn-prepare-payroll-data"); // Mengambil tombol berdasarkan ID
	const payrollPeriodSelected = frm.doc.payroll_period_link;

	// --- KODE DEBUGGING frm.doc ---
	console.log("--- Debugging frm.doc sebelum dikirim ke server ---");
	console.log("Nilai frm.doc yang akan dikirim:", frm.doc);
	console.log("Status checklist di frm.doc:");
	console.log("  payroll_period_link:", frm.doc.payroll_period_link);
	console.log("  checklist_master_active_employees:", frm.doc.checklist_master_active_employees);
	console.log("  checklist_company_holiday_list:", frm.doc.checklist_company_holiday_list);
	console.log("  checklist_daily_attendance_data:", frm.doc.checklist_daily_attendance_data);
	console.log(
		"  checklist_approved_leave_applications:",
		frm.doc.checklist_approved_leave_applications
	);
	console.log(
		"  checklist_perencanaan_lembur_disetujui:",
		frm.doc.checklist_perencanaan_lembur_disetujui
	);
	console.log("  checklist_konfigurasi_hr_settings:", frm.doc.checklist_konfigurasi_hr_settings);
	console.log("--- Akhir Debugging frm.doc ---");

	if (!payrollPeriodSelected) {
		prepareButton.prop("disabled", true);
		frm.set_df_property(
			"button_prepare_payroll_data",
			"description",
			__("Pilih Periode Penggajian terlebih dahulu.")
		);
		return;
	}

	frappe.call({
		doc: frm.doc,
		method: "check_payroll_readiness",
		args: {
			current_doc: frm.doc,
		},
		callback: function (r) {
			console.log("--- Debugging Tombol ---");
			console.log("Status dari check_payroll_readiness (Python):", r.message);
			console.log("Referensi tombol prepareButton (objek jQuery):", prepareButton);
			console.log("Apakah tombol prepareButton ada di DOM?", prepareButton.length > 0);
			console.log(
				"Status disabled tombol sebelum perubahan:",
				prepareButton.prop("disabled")
			);

			if (r.message === true) {
				prepareButton.prop("disabled", false);
				console.log("Perintah: prepareButton.prop('disabled', false) dieksekusi.");
				console.log(
					"Status disabled tombol setelah perintah:",
					prepareButton.prop("disabled")
				);
				frm.set_df_property(
					"button_prepare_payroll_data",
					"description",
					__("Semua prasyarat terpenuhi. Klik untuk menyiapkan data.")
				);
			} else {
				prepareButton.prop("disabled", true);
				console.log("Perintah: prepareButton.prop('disabled', true) dieksekusi.");
				console.log(
					"Status disabled tombol setelah perintah:",
					prepareButton.prop("disabled")
				);
				frm.set_df_property(
					"button_prepare_payroll_data",
					"description",
					__(
						"Centang semua item checklist di atas dan pilih periode penggajian yang valid untuk mengaktifkan tombol."
					)
				);
			}
			console.log("--- Akhir Debugging Tombol ---");
		},
	});
}

function handle_process_start(frm, method, result_field) {
	if (!frm.doc.payroll_period_link) {
		frappe.msgprint(__("Harap pilih Periode Penggajian terlebih dahulu."));
		return;
	}

	// Initial progress bar
	frappe.show_progress(__("Memulai Proses Persiapan Data"), 0, 100);

	frappe.call({
		doc: frm.doc,
		method: method, // This calls enqueue_prepare_payroll_data
		args: {
			// No args needed here as doc is passed via 'doc: frm.doc'
			// and the worker will fetch period details from payroll_period_link
		},
		realtime: true, // Crucial for background job progress
		callback: function (r) {
			frappe.hide_progress();
			frappe.show_alert({
				message: __("Proses selesai! Me-refresh form..."),
				indicator: "green",
			});

			// Reload the entire document from the database to get the latest data.
			// This is the most reliable method.
			frm.reload_doc().then(() => {
				// After the document has successfully reloaded, switch to the result section
				// The payroll_attendance_summary_link (HTML field) will show the link
				frm.scroll_to_field("payroll_attendance_summary_link");
			});
		},
		error: function (r) {
			frappe.hide_progress();
			let error_message = __("Terjadi error saat memanggil proses di server.");
			if (r.exc) {
				error_message += "<br>" + r.exc.split("\n").pop().trim(); // Get last line of traceback
			}
			frappe.show_alert({ message: error_message, indicator: "red" });
		},
		progress: function (data) {
			// Update the progress bar based on backend publications
			if (data.progress) {
				frappe.show_progress(__(data.title || "Memproses..."), data.progress, 100);
			}
		},
	});
}
