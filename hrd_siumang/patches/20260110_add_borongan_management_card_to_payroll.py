import frappe


def execute():
	payroll_workspace = frappe.get_doc("Workspace", "Payroll")
	frappe.msgprint("Memulai patch: Menambahkan Card 'Management Borongan' ke Workspace Payroll")
	frappe.msgprint(
		f"{payroll_workspace.name} memiliki {len(payroll_workspace.links)} link sebelum penambahan."
	)
	# Periksa apakah Card Break "Management Borongan" sudah ada untuk menghindari duplikasi
	card_break_exists = False
	for link_item in payroll_workspace.links:
		if link_item.type == "Card Break" and link_item.label == "Management Borongan":
			card_break_exists = True
			break

	if not card_break_exists:
		# Data untuk Card Break "Management Borongan" dan link-linknya
		new_links_to_add = [
			{
				"type": "Card Break",
				"label": "Management Borongan",
				"hidden": 0,
				"is_query_report": 0,
				"link_count": 4,  # Jumlah DocType Borongan
				"onboard": 0,
			},
			{
				"type": "Link",
				"label": "Input Hasil Borongan",
				"link_to": "Input Hasil Borongan",
				"link_type": "DocType",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
				"is_sub_module": 0,
			},
			{
				"type": "Link",
				"label": "Penugasan Borongan",
				"link_to": "Penugasan Borongan",
				"link_type": "DocType",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
				"is_sub_module": 0,
			},
			{
				"type": "Link",
				"label": "Setup Pekerjaan Borongan",
				"link_to": "Setup Pekerjaan Borongan",
				"link_type": "DocType",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
				"is_sub_module": 0,
			},
			{
				"type": "Link",
				"label": "Tim Borongan",
				"link_to": "Tim Borongan",
				"link_type": "DocType",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
				"is_sub_module": 0,
			},
		]

		# Tambahkan setiap item ke array links di Workspace Payroll
		for item in new_links_to_add:
			payroll_workspace.append("links", item)

		payroll_workspace.save()
		frappe.db.commit()
		frappe.msgprint("Card 'Management Borongan' berhasil ditambahkan ke Workspace Payroll.")
	else:
		frappe.msgprint("Card 'Management Borongan' sudah ada di Workspace Payroll, tidak ada perubahan.")
