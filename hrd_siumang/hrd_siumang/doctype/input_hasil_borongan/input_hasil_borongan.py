# Copyright (c) 2026, Siumang and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InputHasilBorongan(Document):
	def validate(self):
		self.calculate_summary_totals()

	@frappe.whitelist()
	def calculate_summary_totals(self):
		total_dihasilkan = 0
		grand_total_harga = 0
		for item in self.get("detail_hasil_borongan_table"):
			total_dihasilkan += item.jumlah_dihasilkan
			grand_total_harga += item.total_harga_item

		self.summary_total_dihasilkan = total_dihasilkan
		self.summary_grand_total_harga = grand_total_harga


@frappe.whitelist()
def get_pekerjaan_details(pekerjaan_borongan_name):
	details = frappe.get_doc("Setup Pekerjaan Borongan", pekerjaan_borongan_name)
	return {"harga_per_satuan": details.harga_per_satuan, "satuan": details.satuan}
