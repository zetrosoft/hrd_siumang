# Copyright (c) 2026, Bijak Techno and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.model.document import Document
from frappe.model.rename_doc import rename_doc


class BPJSSetting(Document):
	def validate(self):
		self.set_default_components()
		self.sync_component_names()

	def set_default_components(self):
		# TK Defaults with Percentages
		tk_defaults = {
			"JHT Perusahaan": 3.7, 
			"JKK": 0.89, 
			"JKM": 0.3, 
			"JP Perusahaan": 2.0, 
			"JHT Karyawan": 2.0, 
			"JP Karyawan": 1.0
		}
		
		# Update percentages for existing rows or append new ones
		for comp_base, pct in tk_defaults.items():
			found = False
			for row in self.komponen_bpjs_tk:
				if row.salary_component.startswith(comp_base):
					if not row.percentage:
						row.percentage = pct
					found = True
					break
			if not found:
				# Try to find a component that starts with the base name
				existing_comp = frappe.db.get_value("Salary Component", {"name": ["like", f"{comp_base}%"]})
				if existing_comp:
					self.append("komponen_bpjs_tk", {
						"salary_component": existing_comp,
						"percentage": pct
					})
		
		# Kes Defaults with Percentages
		kes_defaults = {
			"JKN Perusahaan": 4.0, 
			"JKN Karyawan": 1.0
		}
		for comp_base, pct in kes_defaults.items():
			found = False
			for row in self.komponen_bpjs_kes:
				if row.salary_component.startswith(comp_base):
					if not row.percentage:
						row.percentage = pct
					found = True
					break
			if not found:
				existing_comp = frappe.db.get_value("Salary Component", {"name": ["like", f"{comp_base}%"]})
				if existing_comp:
					self.append("komponen_bpjs_kes", {
						"salary_component": existing_comp,
						"percentage": pct
					})

	def sync_component_names(self):
		"""Rename Salary Components to include their percentages dynamically."""
		for table_name in ["komponen_bpjs_tk", "komponen_bpjs_kes"]:
			for row in self.get(table_name):
				if not row.salary_component or not row.percentage:
					continue
				
				old_name = row.salary_component
				# Remove existing percentage pattern (e.g., " 4%", " 3.7%", etc.)
				# Pattern looks for a space followed by digits/comma/dot and a percent sign at the end
				base_name = re.sub(r'\s+[\d.,]+%$', '', old_name)
				
				# Format percentage: remove .0 if it's an integer
				pct_str = str(row.percentage).replace('.', ',')
				if pct_str.endswith(',0'):
					pct_str = pct_str[:-2]
				
				new_name = f"{base_name} {pct_str}%"
				
				if old_name != new_name:
					if frappe.db.exists("Salary Component", old_name):
						frappe.flags.silent_rename = True
						rename_doc("Salary Component", old_name, new_name, force=True)
						row.salary_component = new_name
						frappe.msgprint(f"Renamed {old_name} to {new_name}")

	@frappe.whitelist()
	def load_defaults(self):
		self.set_default_components()
		self.save()
		return True

@frappe.whitelist()
def load_defaults():
	doc = frappe.get_doc("BPJS Setting", "BPJS Setting")
	return doc.load_defaults()
