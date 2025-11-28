# Patch 0: Debug Salary Component Creation
import frappe


def execute():
	"""Mencoba membuat satu Salary Component minimal untuk debug."""
	frappe.set_user("Administrator")
	print("Memulai Patch: Debug Salary Component Creation...")

	component_name = "Debug Component"
	if not frappe.db.exists("Salary Component", component_name):
		try:
			doc = frappe.new_doc("Salary Component", name=component_name)
			doc.salary_component_name = component_name
			doc.type = "Earning"  # Tipe wajib
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			print(f"✅ BERHASIL: Debug Component '{component_name}' dibuat.")
		except Exception as e:
			print(f"❌ GAGAL saat membuat Debug Component '{component_name}': {e}")
			frappe.log_error(frappe.get_traceback(), "Debug Salary Component Patch Gagal")
			raise e  # Lemparkan error agar migrate berhenti
	else:
		print(f"[INFO] Debug Component '{component_name}' sudah ada.")

	print("Patch 'debug_salary_component' selesai.")


# -----------------------------------------------------------------------------------
# LAKUKAN INI HANYA JIKA KODE DI ATAS MASIH GAGAL!
# Langkah Terakhir: Hapus semua patch dan jalankan patch dengan hanya menyetel NAME
# Jika ini gagal, itu berarti DocType Salary Component Anda rusak/dimodifikasi.
# -----------------------------------------------------------------------------------
# def execute():
#     frappe.new_doc("Salary Component")
#     frappe.throw("TESTING")
