# Copyright (c) 2026, Siumang and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DetailHasilBorongan(Document):
	def validate(self):
		self.calculate_total_harga_item()

	def calculate_total_harga_item(self):
		self.total_harga_item = self.jumlah_dihasilkan * self.harga_item


@frappe.whitelist()
def get_harian_employees(doctype, txt, searchfield, start, page_len, filters):
	# Filter employees with employment_type = "Harian"
	return frappe.db.sql(
		"""
        SELECT name, employee_name
        FROM `tabEmployee`
        WHERE `employment_type` = 'Harian'
        AND (`name` LIKE %(txt)s OR `employee_name` LIKE %(txt)s)
        ORDER BY `name` ASC
        LIMIT %(page_len)s OFFSET %(start)s
    """,
		{"txt": f"%{txt}%%", "start": start, "page_len": page_len},
	)
