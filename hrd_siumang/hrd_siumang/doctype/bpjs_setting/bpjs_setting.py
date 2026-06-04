# Copyright (c) 2026, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BPJSSetting(Document):
	def validate(self):
		self.set_default_components()

	def set_default_components(self):
		# TK Defaults
		tk_defaults = [
			"JHT Perusahaan 3,7%", 
			"JKK 0,89%", 
			"JKM 0,3%", 
			"JP Perusahaan 2%", 
			"JHT Karyawan 2%", 
			"JP Karyawan 1%"
		]
		existing_tk = [d.salary_component for d in self.komponen_bpjs_tk]
		for comp in tk_defaults:
			if comp not in existing_tk and frappe.db.exists("Salary Component", comp):
				self.append("komponen_bpjs_tk", {"salary_component": comp})
		
		# Kes Defaults
		kes_defaults = [
			"JKN Perusahaan 4%", 
			"JKN Karyawan 1%"
		]
		existing_kes = [d.salary_component for d in self.komponen_bpjs_kes]
		for comp in kes_defaults:
			if comp not in existing_kes and frappe.db.exists("Salary Component", comp):
				self.append("komponen_bpjs_kes", {"salary_component": comp})

@frappe.whitelist()
def load_defaults():
	doc = frappe.get_doc("BPJS Setting", "BPJS Setting")
	doc.set_default_components()
	doc.save()
	return True
