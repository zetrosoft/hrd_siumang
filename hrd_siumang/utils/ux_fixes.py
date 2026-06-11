import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def force_recruitment_ux_improvements():
	"""
	Memaksa perubahan UX Recruitment aktif setiap kali bench migrate dijalankan.
	Mengatasi masalah cache metadata atau kegagalan loading Property Setter JSON.
	"""
	print("Stimulating Recruitment UX Improvements...")

	# 1. PAKSA Rich Text Editor pada Interview Summary
	make_property_setter("Interview", "interview_summary", "fieldtype", "Text Editor", "Select", for_doctype=False)
	
	# 2. PAKSA Rich Text Editor pada Job Applicant (Cover Letter) agar selaras
	make_property_setter("Job Applicant", "cover_letter", "fieldtype", "Text Editor", "Select", for_doctype=False)

	# 3. PAKSA List View Interview agar informatif (Nama & Posisi)
	# Sembunyikan ID pelamar dari list
	make_property_setter("Interview", "job_applicant", "in_list_view", 0, "Check", for_doctype=False)
	# Tampilkan Posisi (Job Opening) di list
	make_property_setter("Interview", "job_opening", "in_list_view", 1, "Check", for_doctype=False)
	
	# 4. Bersihkan Cache Metadata agar perubahan langsung terasa di UI
	frappe.clear_cache(doctype="Interview")
	frappe.clear_cache(doctype="Job Applicant")
	
	print("Recruitment UX Stimulated Successfully.")
