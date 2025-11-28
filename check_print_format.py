import frappe


def check_print_format_status():
	print_format_name = "Slip Gaji Siumang"
	# Cek keberadaan Print Format
	exists = frappe.db.exists("Print Format", print_format_name)
	print(f"Print Format '{print_format_name}' exists: {exists}")

	if exists:
		# Jika ada, coba ambil dan cetak beberapa detail
		try:
			doc = frappe.get_doc("Print Format", print_format_name)
			print(f"DocType: {doc.doc_type}")
			print(f"Module: {doc.module}")
			print(f"Standard: {doc.standard}")
			print(f"HTML (first 100 chars): {doc.html[:100]}...")
		except Exception as e:
			print(f"Error fetching details for {print_format_name}: {e}")
	else:
		print(f"Print Format '{print_format_name}' not found in database.")


if __name__ == "__main__":
	check_print_format_status()
