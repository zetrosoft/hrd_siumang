# Copyright (c) 2026, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BPJSSetting(Document):
	def validate(self):
		self.set_default_components()

	def set_default_components(self):
		# TK Defaults with Percentages
		tk_defaults = {
			"JHT Perusahaan 3,7%": 3.7, 
			"JKK 0,89%": 0.89, 
			"JKM 0,3%": 0.3, 
			"JP Perusahaan 2%": 2.0, 
			"JHT Karyawan 2%": 2.0, 
			"JP Karyawan 1%": 1.0
		}
		
		# Update percentages for existing rows or append new ones
		for comp_name, pct in tk_defaults.items():
			found = False
			for row in self.komponen_bpjs_tk:
				if row.salary_component == comp_name:
					if not row.percentage: # Only update if zero/empty
						row.percentage = pct
					found = True
					break
			if not found and frappe.db.exists("Salary Component", comp_name):
				self.append("komponen_bpjs_tk", {
					"salary_component": comp_name,
					"percentage": pct
				})
		
		# Kes Defaults with Percentages
		kes_defaults = {
			"JKN Perusahaan 4%": 4.0, 
			"JKN Karyawan 1%": 1.0
		}
		for comp_name, pct in kes_defaults.items():
			found = False
			for row in self.komponen_bpjs_kes:
				if row.salary_component == comp_name:
					if not row.percentage: # Only update if zero/empty
						row.percentage = pct
					found = True
					break
			if not found and frappe.db.exists("Salary Component", comp_name):
				self.append("komponen_bpjs_kes", {
					"salary_component": comp_name,
					"percentage": pct
				})

@frappe.whitelist()
def load_defaults():
	doc = frappe.get_doc("BPJS Setting", "BPJS Setting")
	doc.set_default_components()
	doc.save()
	return True
