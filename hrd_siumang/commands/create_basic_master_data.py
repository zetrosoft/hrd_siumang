import frappe


def run():
	company_name = "PT. SIUMANG TEMAN SUKES"
	print(f"--- Creating basic master data for {company_name} ---")

	try:
		# Create Company
		if not frappe.db.exists("Company", company_name):
			try:
				frappe.get_doc(
					{
						"doctype": "Company",
						"company_name": company_name,
						"default_currency": "IDR",  # Assuming IDR as default currency
					}
				).insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"  - Created Company: {company_name}")
			except Exception as e:
				if "Abbreviation already used" in str(e):
					print(
						f"  - ⚠️ WARNING: Could not create Company '{company_name}' due to abbreviation conflict. Please ensure the company exists or create it manually if needed."
					)
					print(f"    Error details: {e}")
				else:
					raise  # Re-raise other errors
		else:
			print(f"  - Company {company_name} already exists.")

		# Create Gender types
		gender_types = ["Laki-Laki", "Perempuan"]
		for gender_name in gender_types:
			if not frappe.db.exists("Gender", gender_name):
				frappe.get_doc({"doctype": "Gender", "gender": gender_name}).insert(ignore_permissions=True)
				print(f"  - Created Gender: {gender_name}")
			else:
				print(f"  - Gender {gender_name} already exists.")
		frappe.db.commit()

		print("--- Basic master data creation finished. ---")

	except Exception as e:
		print(f"A critical error occurred during basic master data creation: {e}")
		frappe.db.rollback()
