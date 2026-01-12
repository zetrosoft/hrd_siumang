from frappe import _


def get_data():
	return [
		{
			"label": _("Laporan Kustom"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"name": "Laporan Borongan Karyawan",
					"doctype": "Input Hasil Borongan",
					"is_query_report": True,
				},
			],
		}
	]
