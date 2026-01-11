// Copyright (c) 2026, Siumang and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Laporan Borongan Karyawan"] = {
	filters: [
		{
			fieldname: "bulan",
			label: __("Bulan & Tahun"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "pekerjaan_borongan",
			label: __("Nama Pekerjaan"),
			fieldtype: "Link",
			options: "Pekerjaan Borongan",
		},
	],
};
