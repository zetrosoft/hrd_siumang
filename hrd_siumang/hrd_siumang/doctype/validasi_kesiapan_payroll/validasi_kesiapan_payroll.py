# Copyright (c) 2025, PT. SIUMANG TEMAN SUKSES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_datetime, getdate, nowdate


class ValidasiKesiapanPayroll(Document):
	WEEKDAY_SCHEMA = "Lembur Hari Kerja"
	WEEKEND_SCHEMA = "Lembur Akhir Pekan"
	HOLIDAY_SCHEMA = "Lembur Libur Resmi"

	@frappe.whitelist()
	def check_payroll_readiness(self, current_doc=None):
		# Gunakan current_doc (yang merupakan dict dari frontend) jika disediakan, jika tidak, kembali ke self (objek Dokumen)
		# Ini memastikan kita selalu membaca nilai terbaru dari frontend
		source = frappe._dict(current_doc) if current_doc else self

		frappe.log_error(
			f"Memanggil check_payroll_readiness untuk dokumen: {source.get('name')}", "Debug Checklist"
		)
		frappe.log_error(f"  payroll_period_link: {source.get('payroll_period_link')}", "Debug Checklist")
		frappe.log_error(
			f"  checklist_master_active_employees: {source.get('checklist_master_active_employees')}",
			"Debug Checklist",
		)
		frappe.log_error(
			f"  checklist_company_holiday_list: {source.get('checklist_company_holiday_list')}",
			"Debug Checklist",
		)
		frappe.log_error(
			f"  checklist_daily_attendance_data: {source.get('checklist_daily_attendance_data')}",
			"Debug Checklist",
		)
		frappe.log_error(
			f"  checklist_approved_leave_applications: {source.get('checklist_approved_leave_applications')}",
			"Debug Checklist",
		)
		frappe.log_error(
			f"  checklist_perencanaan_lembur_disetujui: {source.get('checklist_perencanaan_lembur_disetujui')}",
			"Debug Checklist",
		)
		frappe.log_error(
			f"  checklist_konfigurasi_hr_settings: {source.get('checklist_konfigurasi_hr_settings')}",
			"Debug Checklist",
		)

		# Pastikan payroll_period_link juga dicentang/terisi
		payroll_period_link_value = source.get("payroll_period_link")
		if not payroll_period_link_value:
			frappe.log_error("  Payroll Period Link kosong.", "Debug Checklist")
			return False

		checklist_values = [
			source.get("checklist_master_active_employees"),
			source.get("checklist_company_holiday_list"),
			source.get("checklist_daily_attendance_data"),
			source.get("checklist_approved_leave_applications"),
			source.get("checklist_perencanaan_lembur_disetujui"),
			source.get("checklist_konfigurasi_hr_settings"),
		]

		# Pastikan semua item secara eksplisit 1 (True), bukan hanya truthy (karena 0 adalah falsy)
		all_items_checked = all(item == 1 for item in checklist_values)

		frappe.log_error(f"  Hasil dari all(checklist_values): {all_items_checked}", "Debug Checklist")
		return all_items_checked

	@frappe.whitelist()
	def enqueue_prepare_payroll_data(self):
		"""
		Enqueues a background job to prepare all payroll attendance data.
		Performs initial validation on checklist and selected period.
		"""
		if not self.payroll_period_link:
			frappe.throw("Pilih Periode Penggajian terlebih dahulu.")

		# Optional: Add server-side re-check of checklist if needed for extra security
		# if not self.check_payroll_readiness():
		# 	frappe.throw("Semua item checklist harus dicentang sebelum melanjutkan.")

		frappe.enqueue(
			"hrd_siumang.hrd_siumang.doctype.validasi_kesiapan_payroll.validasi_kesiapan_payroll._execute_prepare_payroll_data",
			queue="long",
			timeout=3600,  # Increased timeout for potentially long process
			job_name=f"prepare-payroll-data-{self.payroll_period_link}",
			docname=self.name,  # Pass the name of the Validasi Kesiapan Payroll doc
			payroll_period_name=self.payroll_period_link,
			is_async=True,
		)


# --- Background Job Worker Function (Unified) ---


def _execute_prepare_payroll_data(docname, payroll_period_name):
	# Get the DocType instance for Validasi Kesiapan Payroll
	validation_doc = frappe.get_doc("Validasi Kesiapan Payroll", docname)

	# Get the Payroll Period instance to extract start/end dates
	payroll_period_doc = frappe.get_doc("Payroll Period", payroll_period_name)
	start_date = getdate(payroll_period_doc.start_date)
	end_date = getdate(payroll_period_doc.end_date)

	try:
		frappe.publish_progress(0, title="Memulai Persiapan Data Payroll...")

		# Step 1: Clear existing Payroll Attendance Summary for this period
		frappe.publish_progress(5, title="Membersihkan Ringkasan Kehadiran Payroll lama...")
		_clear_existing_payroll_attendance_summary(payroll_period_name)

		# Step 2: Fetch all necessary raw data in bulk
		frappe.publish_progress(10, title="Mengambil data sumber...")
		employees = frappe.get_all(
			"Employee", filters={"status": "Active"}, fields=["name", "company", "holiday_list"]
		)
		if not employees:
			return "Tidak ada karyawan aktif yang ditemukan."

		employee_names = [e.name for e in employees]
		_employee_map = {e.name: e for e in employees}  # For quick lookup

		# Fetch all relevant Attendance records for the period
		all_attendance = frappe.get_all(
			"Attendance",
			filters={
				"employee": ["in", employee_names],
				"attendance_date": ["between", [start_date, end_date]],
			},
			fields=["name", "employee", "attendance_date", "status"],
			as_dict=True,
		)
		attendance_map = {(att.employee, att.attendance_date): att for att in all_attendance}

		# Fetch all relevant Leave Applications for the period
		all_leave_applications = frappe.get_all(
			"Leave Application",
			filters={
				"employee": ["in", employee_names],
				"docstatus": 1,
				"from_date": ["<=", end_date],
				"to_date": [">=", start_date],
			},
			fields=["name", "employee", "leave_type", "from_date", "to_date", "half_day", "leave_type"],
			as_dict=True,
		)
		leave_app_map = {}
		for la in all_leave_applications:
			# Expand leave applications to individual days
			current_la_date = getdate(la.from_date)
			while current_la_date <= getdate(la.to_date):
				# Handle half-day logic, or just mark the day as on leave
				leave_app_map[(la.employee, current_la_date)] = la
				current_la_date = add_days(current_la_date, 1)

		# Fetch all relevant Overtime Planning details
		all_overtime_details = frappe.get_all(
			"Overtime Planning Detail",
			filters={"parenttype": "Overtime Planning", "employee": ["in", employee_names], "docstatus": 1},
			join_wheres=[f"(`tabOvertime Planning`.overtime_date BETWEEN '{start_date}' AND '{end_date}')"],
			fields=["name", "parent", "employee", "start_time", "end_time"],
			as_dict=True,
		)
		# Link back to parent Overtime Planning for the date
		overtime_map = {}
		for od in all_overtime_details:
			parent_plan_date = frappe.db.get_value("Overtime Planning", od.parent, "overtime_date")
			if (
				parent_plan_date
				and getdate(parent_plan_date) >= start_date
				and getdate(parent_plan_date) <= end_date
			):
				if (od.employee, parent_plan_date) not in overtime_map:
					overtime_map[(od.employee, parent_plan_date)] = []
				overtime_map[(od.employee, parent_plan_date)].append(od)

		# Cache HR Settings and Overtime Rates
		_hr_settings = frappe.get_single("HR Settings")
		_overtime_rates_config = _get_overtime_rates_config(
			validation_doc
		)  # Use validation_doc context for schemas

		# Step 3: Iterate through each employee and each day in the period
		frappe.publish_progress(20, title="Memproses kehadiran per karyawan dan per hari...")
		total_days_in_period = (end_date - start_date).days + 1
		total_active_employees = len(employees)
		total_iterations = total_active_employees * total_days_in_period
		processed_count = 0

		new_summary_docs = []

		for _emp_idx, employee_data in enumerate(employees):
			employee_name = employee_data.name

			current_date = start_date
			while current_date <= end_date:
				processed_count += 1
				if processed_count % 100 == 0:  # Update progress every 100 iterations
					frappe.publish_progress(
						20 + int(processed_count / total_iterations * 70),
						title=f"Memproses {employee_name} ({current_date})...",
					)

				summary = frappe.new_doc("Payroll Attendance Summary")
				summary.payroll_period = payroll_period_name
				summary.employee = employee_name
				summary.attendance_date = current_date
				summary.attendance_status = "Absen"  # Default to Absent

				# Determine Holiday Status
				is_holiday = _is_holiday_for_employee(employee_data, current_date)
				if is_holiday:
					summary.attendance_status = "Holiday"
					summary.source_leave_doc = frappe.db.get_value(
						"Holiday", {"holiday_date": current_date, "parent": employee_data.holiday_list}
					)

				# Determine Leave Status (overrides Holiday if employee is on leave)
				leave_app_data = leave_app_map.get((employee_name, current_date))
				if leave_app_data:
					summary.attendance_status = "On Leave"
					summary.source_leave_doc = leave_app_data.name
					if leave_app_data.leave_type == "Leave Without Pay":  # Assuming LWP leave type
						summary.is_lwp = 1

				# Determine Attendance Status (overrides Leave/Holiday)
				attendance_data = attendance_map.get((employee_name, current_date))
				if attendance_data:
					summary.attendance_status = attendance_data.status
					summary.source_absensi_doc = attendance_data.name
					if attendance_data.status == "Absent":  # If marked Absent in Attendance, check LWP
						current_leave_balance = (
							frappe.db.get_value(
								"Leave Ledger Entry",
								{"employee": employee_name, "leave_type": "Cuti Tahunan"},
								"sum(leaves)",
							)
							or 0
						)
						if current_leave_balance <= 0:
							summary.is_lwp = 1  # Mark as LWP if absent and no leave balance

				# Determine Overtime Hours
				overtime_details_for_day = overtime_map.get((employee_name, current_date), [])
				if overtime_details_for_day:
					total_ot_duration = 0.0
					for ot_detail in overtime_details_for_day:
						start_dt = get_datetime(f"{current_date} {ot_detail.start_time}")
						end_dt = get_datetime(f"{current_date} {ot_detail.end_time}")
						if end_dt < start_dt:
							end_dt = add_days(end_dt, 1)
						total_ot_duration += (end_dt - start_dt).total_seconds() / 3600
					summary.overtime_hours = total_ot_duration
					summary.source_overtime_doc = overtime_details_for_day[
						0
					].parent  # Link to first Overtime Planning doc for simplicity

				new_summary_docs.append(summary)
				current_date = add_days(current_date, 1)

		# Step 4: Save all generated summary documents
		frappe.publish_progress(90, title="Menyimpan Ringkasan Kehadiran Payroll...")
		for summary_doc in new_summary_docs:
			summary_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.publish_progress(100, title="Selesai! Data siap.")
		return f"Data kehadiran payroll untuk periode {payroll_period_name} telah berhasil disiapkan."

	except Exception:
		tb = frappe.get_traceback()
		validation_doc.log_error(
			f"Gagal menyiapkan data kehadiran payroll untuk periode {payroll_period_name}", tb
		)
		return f"<h4>Error</h4><p>Terjadi kesalahan saat menyiapkan data kehadiran payroll. Silakan cek Error Log.</p><pre>{tb}</pre>"


# --- HELPER FUNCTIONS (Adapted for new unified process) ---


def _clear_existing_payroll_attendance_summary(payroll_period_name):
	"""Clears existing Payroll Attendance Summary records for a given period."""
	existing_records = frappe.get_all(
		"Payroll Attendance Summary", filters={"payroll_period": payroll_period_name}, fields=["name"]
	)
	for record in existing_records:
		frappe.delete_doc("Payroll Attendance Summary", record.name, ignore_permissions=True, force=True)
	frappe.db.commit()


def _is_holiday_for_employee(employee_data, current_date):
	holiday_list_name = employee_data.holiday_list
	if holiday_list_name:
		holiday_docs = frappe.get_all(
			"Holiday", filters={"holiday_date": current_date, "parent": holiday_list_name}, fields=["name"]
		)
		return bool(holiday_docs)
	return False


def _get_overtime_rates_config(doc):
	"""
	Loads and validates Overtime Calculation configurations for different day types.
	Throws an error if any required schema is missing or incomplete.
	"""
	overtime_rates_config = {}
	schema_names = {
		"Hari Kerja": doc.WEEKDAY_SCHEMA,
		"Akhir Pekan": doc.WEEKEND_SCHEMA,
		"Hari Libur Nasional": doc.HOLIDAY_SCHEMA,
	}

	for day_type, schema_name in schema_names.items():
		overtime_calc_doc_name = frappe.db.get_value(
			"Overtime Calculation", {"nama_skema": schema_name}, "name"
		)
		if not overtime_calc_doc_name:
			frappe.throw(
				f"DocType 'Overtime Calculation' tidak memiliki skema tarif lembur untuk '{schema_name}'. "
				"Harap siapkan data ini terlebih dahulu."
			)
		full_overtime_calc_doc = frappe.get_doc("Overtime Calculation", overtime_calc_doc_name)
		if not full_overtime_calc_doc.overtime_rates:
			frappe.throw(
				f"Skema lembur '{schema_name}' tidak memiliki tarif lembur yang terdaftar. "
				"Harap tambahkan setidaknya satu tarif lembur."
			)

		# Sort rates by jam_ke_mulai to ensure correct tiered processing
		overtime_rates_config[day_type] = sorted(
			full_overtime_calc_doc.overtime_rates, key=lambda x: x.jam_ke_mulai
		)
	return overtime_rates_config


# Remaining helper functions from original file.
# Note: _is_expected_to_work_on_day and _calculate_tiered_overtime_pay might not be directly used
# in the new _execute_prepare_payroll_data as it takes a different approach,
# but keeping them for now if they are used elsewhere or in a more refined version.
# For simplicity, I'm adapting _is_holiday_for_employee as a direct check.
