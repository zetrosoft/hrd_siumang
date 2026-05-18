import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_install():
	"""
	Fungsi ini dijalankan setelah aplikasi 'hrd_siumang' diinstal.
	Ini akan menambahkan Property Setter untuk field 'no_of_positions'
	pada DocType 'Job Requisition'.
	"""

	# JSON yang Anda berikan
	property_setter_json = {
		"doctype": "Property Setter",
		"doctype_or_field": "DocField",
		"field_name": "no_of_positions",
		"name": "Job Requisition-no_of_positions-description",
		"property": "description",
		"value": "Jumlah yang dibutuhkan untuk posisi ini",
		"dt": "Job Requisition",
		"description": "Jumlah yang dibutuhkan untuk posisi ini",
	}

	# Cek apakah Property Setter sudah ada untuk menghindari duplikasi
	if not frappe.db.exists("Property Setter", property_setter_json["name"]):
		try:
			# Mengambil dokumen dari JSON dan menyimpannya ke database
			doc = frappe.get_doc(property_setter_json)
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.clear_cache()
			frappe.msgprint("Deskripsi field 'no_of_positions' telah ditambahkan.")
		except Exception as e:
			frappe.log_error(title="Gagal Menambahkan Property Setter", message=str(e))
			frappe.msgprint("Gagal menambahkan deskripsi field.")
