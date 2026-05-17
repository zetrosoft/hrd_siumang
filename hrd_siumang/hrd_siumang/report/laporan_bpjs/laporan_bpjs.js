frappe.query_reports["Laporan BPJS"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Bulan"),
			"fieldtype": "Select",
			"options": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12",
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
		},
		{
			"fieldname": "year",
			"label": __("Tahun"),
			"fieldtype": "Select",
			"reqd": 1,
			"options": "2024\n2025\n2026\n2027\n2028\n2029\n2030",
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getFullYear()
		},
		{
			"fieldname": "employee",
			"label": __("Karyawan"),
			"fieldtype": "Link",
			"options": "Employee"
		}
	]
};