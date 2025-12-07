// Copyright (c) 2025, PT. SIUMANG TEMAN SUKSES and contributors
// For license information, please see license.txt

frappe.ui.form.on("Validasi Kesiapan Payroll", {
	refresh: function (frm) {
		// Hapus semua tombol custom yang ada untuk menghindari duplikasi
		frm.clear_custom_buttons();

		// Tambahkan tombol "Proses Absensi" (Aksi Utama - standalone)
		frm.add_custom_button(__("Proses Absensi"), function () {
			// Periksa apakah tanggal sudah diisi
			if (!frm.doc.start_date || !frm.doc.end_date) {
				frappe.msgprint({
					title: __("Input Diperlukan"),
					indicator: "orange",
					message: __("Harap tentukan Start Date dan End Date sebelum memulai proses."),
				});
				return;
			}

			frappe.confirm(
				'Anda yakin ingin memulai proses Validasi Absensi?<br><br>Sistem akan melakukan langkah-langkah berikut:<br><ul><li>Membersihkan semua data absensi dan pengajuan cuti untuk periode yang dipilih.</li><li>Mengidentifikasi hari kerja setiap karyawan berdasarkan daftar hari libur dan penugasan shift.</li><li>Mencatat hari kerja tanpa kehadiran sebagai "Absent".</li><li>Mengonversi "Absent" menjadi "Cuti" jika saldo cuti tersedia.</li></ul>Ringkasan hasil proses akan ditampilkan setelah selesai.',
				function () {
					// Tampilkan indikator proses
					frappe.show_progress(
						__("Memproses"),
						__("Memvalidasi data absensi..."),
						__("Mohon tunggu")
					);

					// Panggil metode Python di sisi server
					frappe.call({
						method: "run_absence_validation_logic",
						doc: frm.doc, // Mengirim seluruh dokumen sebagai konteks
						callback: function (r) {
							frappe.hide_progress();
							if (r.message) {
								// 1. Update properti tampilan field HTML secara langsung
								frm.set_df_property("hasil_validasi", "options", r.message);
								// 2. Update objek dokumen untuk memastikan nilai tersimpan
								frm.doc.hasil_validasi = r.message;

								// 3. Simpan dokumen untuk mem-persist perubahan
								frm.save({
									callback: function (save_response) {
										if (save_response && !save_response.exc) {
											// Periksa penyimpanan yang berhasil
											frappe.msgprint({
												title: __("Proses Selesai & Tersimpan"),
												indicator: "green",
												message: __(
													"Hasil validasi telah disimpan. Memuat ulang form..."
												),
											});
											// Muat ulang form untuk menampilkan konten HTML yang disimpan secara persisten
											frm.reload_doc();
										} else {
											frappe.msgprint({
												title: __("Error Saat Menyimpan"),
												indicator: "red",
												message: __(
													"Terjadi error saat menyimpan hasil validasi. Silakan cek Error Log."
												),
											});
										}
									},
									freeze: true,
									freeze_message: __("Menyimpan hasil validasi..."),
								});
							} else {
								frappe.msgprint({
									title: __("Proses Selesai"),
									indicator: "blue",
									message: __("Tidak ada pesan hasil dari server."),
								});
							}
						},
						error: function (r) {
							frappe.hide_progress();
							frappe.msgprint({
								title: __("Error Umum"),
								indicator: "red",
								message: __(
									"Terjadi error saat memproses. Silakan cek Error Log untuk detail."
								),
							});
						},
					});
				}
			);
		}); // Tombol "Proses Absensi" tanpa grup

		// Tambahkan tombol "Laporan Lembur" (dalam grup Laporan)
		frm.add_custom_button(
			__("Laporan Lembur"),
			function () {
				if (!frm.doc.start_date || !frm.doc.end_date) {
					frappe.msgprint({
						title: __("Input Diperlukan"),
						indicator: "orange",
						message: __("Harap tentukan Start Date dan End Date terlebih dahulu."),
					});
					return;
				}
				frappe.show_progress(
					__("Memproses"),
					__("Menghasilkan laporan lembur..."),
					__("Mohon tunggu")
				);
				frappe.call({
					method: "get_overtime_report_data",
					doc: frm.doc,
					callback: function (r) {
						frappe.hide_progress();
						if (r.message) {
							frm.set_df_property("hasil_validasi", "options", r.message);
							frm.doc.hasil_validasi = r.message; // Update doc for potential save if user clicks save manually
							frappe.msgprint({
								title: __("Laporan Lembur Siap"),
								indicator: "green",
								message: __("Laporan lembur telah dimuat di bawah."),
							});
						} else {
							frappe.msgprint({
								title: __("Laporan Lembur"),
								indicator: "blue",
								message: __("Tidak ada data lembur untuk ditampilkan."),
							});
						}
					},
					error: function (r) {
						frappe.hide_progress();
						frappe.msgprint({
							title: __("Error Laporan Lembur"),
							indicator: "red",
							message: __(
								"Terjadi error saat mengambil laporan lembur. Silakan cek Error Log."
							),
						});
					},
				});
			},
			__("Laporan")
		); // Group for reports

		// Tambahkan tombol "Laporan Cuti" (dalam grup Laporan)
		frm.add_custom_button(
			__("Laporan Cuti"),
			function () {
				if (!frm.doc.start_date || !frm.doc.end_date) {
					frappe.msgprint({
						title: __("Input Diperlukan"),
						indicator: "orange",
						message: __("Harap tentukan Start Date dan End Date terlebih dahulu."),
					});
					return;
				}
				frappe.show_progress(
					__("Memproses"),
					__("Menghasilkan laporan cuti..."),
					__("Mohon tunggu")
				);
				frappe.call({
					method: "get_leave_report_data",
					doc: frm.doc,
					callback: function (r) {
						frappe.hide_progress();
						if (r.message) {
							frm.set_df_property("hasil_validasi", "options", r.message);
							frm.doc.hasil_validasi = r.message; // Update doc for potential save if user clicks save manually
							frappe.msgprint({
								title: __("Laporan Cuti Siap"),
								indicator: "green",
								message: __("Laporan cuti telah dimuat di bawah."),
							});
						} else {
							frappe.msgprint({
								title: __("Laporan Cuti"),
								indicator: "blue",
								message: __("Tidak ada data cuti untuk ditampilkan."),
							});
						}
					},
					error: function (r) {
						frappe.hide_progress();
						frappe.msgprint({
							title: __("Error Laporan Cuti"),
							indicator: "red",
							message: __(
								"Terjadi error saat mengambil laporan cuti. Silakan cek Error Log."
							),
						});
					},
				});
			},
			__("Laporan")
		); // Group for reports
	},
});
