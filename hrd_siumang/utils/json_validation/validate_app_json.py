import json
import os

import frappe


def validate_hrd_siumang_json_files():
	app_path = frappe.get_app_path("hrd_siumang")
	json_files_to_check = []

	# Collect all .json files under doctype, fixtures, and property_setters
	for root, _, files in os.walk(os.path.join(app_path, "hrd_siumang")):
		for file in files:
			if file.endswith(".json"):
				json_files_to_check.append(os.path.join(root, file))

	# Also include files from the main fixtures folder if they are JSON
	for root, _, files in os.walk(os.path.join(app_path, "fixtures")):
		for file in files:
			if file.endswith(".json"):
				json_files_to_check.append(os.path.join(root, file))

	print(f"--- Validating {len(json_files_to_check)} JSON files in hrd_siumang app ---")

	errors_found = False
	for file_path in json_files_to_check:
		try:
			with open(file_path, encoding="utf-8") as f:
				content = f.read()
				# Try to parse as JSON
				json.loads(content)
			print(f"✅ Valid JSON: {file_path}")
		except json.JSONDecodeError as e:
			print(f"❌ Invalid JSON: {file_path} - {e}")
			errors_found = True
		except Exception as e:
			print(f"❌ Error reading {file_path}: {e}")
			errors_found = True

	if errors_found:
		print("\nJSON validation FAILED for hrd_siumang app.")
	else:
		print("\nAll JSON files in hrd_siumang app are valid.")

	return errors_found


if __name__ == "__main__":
	# This block allows direct execution or via bench execute
	# For bench execute: bench --site your_site_name execute validate_app_json.validate_hrd_siumang_json_files
	# For direct python: Ensure frappe context is available or mock it for testing
	validate_hrd_siumang_json_files()
