// Copyright (c) 2025, Bijak Techno and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Allowance Data", {
	refresh(frm) {
		// Set status message on load
		if (frm.doc.employee) {
			frm.trigger("get_calculated_denominator");
		}
	},
	employee(frm) {
		if (frm.doc.employee) {
			frm.trigger("get_calculated_denominator");
		} else {
			frm.set_value("manual_payroll_denominator", 0);
			frm.set_df_property("manual_payroll_denominator", "description", "");
		}
	},
	get_calculated_denominator(frm) {
		frappe.call({
			method: "hrd_siumang.payroll.payroll_utils.get_payroll_denominator_info",
			args: {
				employee: frm.doc.employee
			},
			callback: function(r) {
				if (r.message) {
					const info = r.message;
					
					if (!info.has_shift) {
						frappe.msgprint({
							title: __('Shift Belum Diatur'),
							indicator: 'orange',
							message: __('Karyawan <b>{0}</b> belum ditautkan ke Shift Type aktif. Harap atur <b>Shift Assignment</b> atau <b>Default Shift</b> pada Karyawan agar perhitungan pembagi hari kerja otomatis muncul dengan tepat.', [frm.doc.employee])
						});
						frm.set_df_property("manual_payroll_denominator", "description", 
							`<span class='label label-danger'>Shift Tidak Terdeteksi</span>`
						);
					} else {
						// Auto-fill denominator if it's a new record or if current value is 0
						if (frm.is_new() || !frm.doc.manual_payroll_denominator) {
							frm.set_value("manual_payroll_denominator", info.denominator);
						}
						
						// Provide visual feedback about system value
						let status_label = (frm.doc.manual_payroll_denominator != info.denominator ? 
							`<span class='label label-warning'>Nilai Sistem (${info.denominator}) Diabaikan</span>` : 
							`<span class='label label-success'>Nilai Sistem (${info.denominator}) Aktif</span>`);
						
						let detail_info = `<div style='margin-top: 5px; font-size: 0.85em; color: #666;'>
							<b>Detail Sumber Perhitungan:</b><br>
							• Shift: <i>${info.shift}</i> (${info.source})<br>
							• Kalender: <i>${info.holiday_list}</i>
						</div>`;
						
						frm.set_df_property("manual_payroll_denominator", "description", status_label + detail_info);
					}
				}
			}
		});
	},
	manual_payroll_denominator(frm) {
		if (frm.doc.employee) {
			frm.trigger("get_calculated_denominator");
		}
	}
});
