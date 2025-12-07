# Copyright (c) 2025, PT. SIUMANG TEMAN SUKSES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_datetime, get_time, getdate, nowdate


class ValidasiKesiapanPayroll(Document):
	WEEKDAY_SCHEMA = "Lembur Hari Kerja"  # Updated to match fixture
	WEEKEND_SCHEMA = "Lembur Akhir Pekan"  # Needs a fixture
	HOLIDAY_SCHEMA = "Lembur Libur Resmi"  # Updated to match fixture

	def _clear_existing_attendance_and_leaves(self, start_date, end_date, employee_names=None):
		"""
		Clears existing Attendance and Leave Application records for the given period and employees.
		Returns a dictionary with counts of deleted records.
		"""
		deleted_attendance_count = 0
		deleted_leave_app_count = 0

		filters = {
			"attendance_date": ["between", [start_date, end_date]],
		}
		if employee_names:
			filters["employee"] = ["in", employee_names]

		# Delete Attendance records
		attendances_to_delete = frappe.get_all("Attendance", filters=filters, fields=["name"])
		for att in attendances_to_delete:
			frappe.delete_doc("Attendance", att.name, ignore_permissions=True, force=True)
			deleted_attendance_count += 1
		frappe.db.commit()  # Commit deletes immediately

		# Delete Leave Application records (only those created by this process or manual for these dates)
		# We can filter by description to only delete auto-created ones, or delete all for the period.
		# For now, let's delete all Leave Applications for the period and employees for a clean slate.
		leave_app_filters = {
			"from_date": ["<=", end_date],
			"to_date": [">=", start_date],
		}
		if employee_names:
			leave_app_filters["employee"] = ["in", employee_names]

		leave_apps_to_delete = frappe.get_all("Leave Application", filters=leave_app_filters, fields=["name"])
		for la in leave_apps_to_delete:
			try:
				frappe.delete_doc("Leave Application", la.name, ignore_permissions=True, force=True)
				deleted_leave_app_count += 1
			except Exception as e:
				frappe.log_error(
					frappe.get_traceback(), f"Failed to delete Leave Application {la.name}: {e!s}"
				)

		frappe.db.commit()  # Commit deletes immediately

		return {"attendance": deleted_attendance_count, "leave_application": deleted_leave_app_count}

	def _is_expected_to_work_on_day(
		self,
		employee_doc,
		current_date,
		company_holiday_cache,
		employee_shift_cache,
	):
		"""
		Helper function to determine if an employee is expected to work on a given date.
		Returns (is_expected_to_work, has_shift_assigned, is_holiday, is_weekend).
		"""
		is_expected_to_work = False
		has_shift_assigned = False
		is_holiday = False
		is_weekend = current_date.weekday() in [5, 6]  # 5 is Saturday, 6 is Sunday

		# A. Check Holiday List
		holiday_list_name = employee_doc.holiday_list
		if holiday_list_name:
			if holiday_list_name not in company_holiday_cache:
				holiday_docs = frappe.get_all(
					"Holiday", filters={"parent": holiday_list_name}, fields=["holiday_date"]
				)
				company_holiday_cache[holiday_list_name] = {h.holiday_date for h in holiday_docs}

			if current_date in company_holiday_cache.get(holiday_list_name, {}):
				is_holiday = True
				# If it's a holiday, employee is not expected to work (unless specified otherwise, but default is no work)
				return False, False, True, is_weekend

		# B. Check Shift Assignment for the specific day (Simplified: assumes shift means work on weekdays)
		shift_key = (employee_doc.name, current_date)
		if shift_key not in employee_shift_cache:
			shift_assignment = frappe.get_all(
				"Shift Assignment",
				filters={
					"employee": employee_doc.name,
					"start_date": ["<=", current_date],
					"end_date": [">=", current_date],
					"docstatus": 1,  # Only active assignments
				},
				fields=["shift_type"],
				limit=1,
			)
			employee_shift_cache[shift_key] = shift_assignment[0].shift_type if shift_assignment else None

		assigned_shift_type = employee_shift_cache.get(shift_key)

		if assigned_shift_type:
			has_shift_assigned = True
			is_expected_to_work = not is_weekend  # Assumes shift workers follow Mon-Fri unless weekend
		else:
			# Fallback to general working day check (Mon-Fri) if no specific shift assigned
			is_expected_to_work = not is_weekend

		return is_expected_to_work, has_shift_assigned, is_holiday, is_weekend

	def _calculate_tiered_overtime_pay(
		self,
		overtime_duration_hours,
		base_hourly_rate,
		rates_for_day_type,
	):
		"""
		Calculates overtime pay based on tiered rates for a specific day type.
		`rates_for_day_type` is a sorted list of {jam_ke_mulai, jam_ke_selesai, pengali_upah}.
		"""
		total_overtime_pay = 0.0
		remaining_duration_to_pay = flt(overtime_duration_hours)

		# Iterate through the actual overtime hours
		current_ot_hour_index = 0.0  # From 0.0 to overtime_duration_hours

		while remaining_duration_to_pay > 0.001:  # Use small epsilon for float comparison
			# Determine the current hour being processed (1st, 2nd, 3rd, etc.)
			current_tier_hour_num = int(current_ot_hour_index) + 1  # 1st hour, 2nd hour, etc.

			# Find the rate for this specific hour
			applicable_multiplier = 1.0  # Default if no tier matches (should log a warning)
			found_tier = False
			for rate_tier in rates_for_day_type:
				if rate_tier.jam_ke_mulai <= current_tier_hour_num <= rate_tier.jam_ke_selesai:
					applicable_multiplier = rate_tier.pengali_upah
					found_tier = True
					break

			if not found_tier:
				# If no specific rate is defined for higher hours, use 1x multiplier and log a warning
				frappe.log_error(
					message=f"No overtime rate found for hour {current_tier_hour_num} and beyond. Defaulting to 1.0x. "
					f"Overtime duration: {overtime_duration_hours:.2f} hrs. Defined tiers might be insufficient.",
					title="Overtime Calculation Warning",
				)
				# We still want to pay for this duration, so applicable_multiplier remains 1.0

			# Calculate how much duration will be paid in this segment (up to next full hour, or remaining duration)
			duration_in_current_segment = min(
				remaining_duration_to_pay, flt(int(current_ot_hour_index) + 1) - current_ot_hour_index
			)

			total_overtime_pay += duration_in_current_segment * base_hourly_rate * applicable_multiplier
			remaining_duration_to_pay -= duration_in_current_segment
			current_ot_hour_index += duration_in_current_segment  # Advance the hour index

		return total_overtime_pay

	@frappe.whitelist()
	def run_absence_validation_logic(self):
		"""
		Finds all 'Absent' attendance records within the specified date range and attempts
		to convert them to 'On Leave' if the employee has a sufficient leave balance.
		Also creates 'Absent' attendance records for employees who were expected to work
		but have no attendance records for a given working day, considering Holiday List.
		Shift Assignment integration is simplified for initial DocType loading.
		"""
		frappe.log_error(message="run_absence_validation_logic function called.", title="HRD Siumang Debug")

		if not self.start_date or not self.end_date:
			frappe.throw("Harap tentukan Start Date dan End Date terlebih dahulu.")

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		active_employees_data = frappe.get_all(
			"Employee", filters={"status": "Active"}, fields=["name", "company", "holiday_list"]
		)
		if not active_employees_data:
			frappe.msgprint("Tidak ditemukan karyawan aktif.")
			return

		active_employee_names = [emp.name for emp in active_employees_data]

		# --- Clear existing data for the period ---
		clear_counts = self._clear_existing_attendance_and_leaves(start_date, end_date, active_employee_names)
		frappe.log_error(
			message=f"Cleared {clear_counts['attendance']} Attendance and {clear_counts['leave_application']} Leave Applications.",
			title="HRD Siumang Debug",
		)

		total_active_employees = len(active_employees_data)
		total_days_in_period = (end_date - start_date).days + 1

		period_working_days_count = 0
		period_holiday_days_count = 0
		employees_on_shift_in_period = set()
		employees_without_shift_in_period = set()

		# total_potential_overtime_hours = 0.0 # Placeholder for future calculation

		company_holiday_cache = {}
		employee_shift_cache = {}

		created_implicit_absent_count = 0
		total_potential_overtime_hours = 0.0  # Initialize placeholder

		current_date = start_date
		while current_date <= end_date:
			is_any_employee_working_today = False
			is_any_employee_on_holiday_today = False

			for emp_data in active_employees_data:
				is_expected_to_work_on_this_day, has_shift_assigned, is_holiday_today, _is_weekend_today = (
					self._is_expected_to_work_on_day(
						emp_data, current_date, company_holiday_cache, employee_shift_cache
					)
				)

				if has_shift_assigned:
					employees_on_shift_in_period.add(emp_data.name)
				else:
					employees_without_shift_in_period.add(emp_data.name)

				if is_holiday_today:
					is_any_employee_on_holiday_today = True

				if is_expected_to_work_on_this_day:
					is_any_employee_working_today = True

					existing_attendance = frappe.db.exists(
						"Attendance", {"employee": emp_data.name, "attendance_date": current_date}
					)

					if not existing_attendance:
						try:
							absent_doc = frappe.new_doc("Attendance")
							absent_doc.employee = emp_data.name
							absent_doc.attendance_date = current_date
							absent_doc.status = "Absent"
							absent_doc.late_entry = 0
							absent_doc.early_exit = 0
							absent_doc.insert(ignore_permissions=True)
							created_implicit_absent_count += 1
						except Exception as e:
							frappe.log_error(
								frappe.get_traceback(),
								f"Failed to create implicit Absent attendance for {emp_data.name} on {current_date}: {e!s}",
							)

			if is_any_employee_working_today:
				period_working_days_count += 1
			if is_any_employee_on_holiday_today:
				period_holiday_days_count += 1

			current_date = add_days(current_date, 1)

		frappe.log_error(
			message=f"Created {created_implicit_absent_count} implicit absent records.",
			title="HRD Siumang Debug",
		)

		absent_attendances = frappe.get_all(
			"Attendance",
			filters={
				"status": "Absent",
				"attendance_date": ["between", [start_date, end_date]],
			},
			fields=["name", "employee", "attendance_date"],
		)

		frappe.log_error(
			message=f"Found total {len(absent_attendances)} absent attendance records (including newly created) for leave conversion.",
			title="HRD Siumang Debug",
		)

		if not absent_attendances and created_implicit_absent_count == 0:
			frappe.msgprint(
				"Tidak ditemukan data absensi dengan status 'Absent' pada periode ini, dan tidak ada absensi implisit yang dibuat."
			)
			return

		converted_count = 0
		lwp_count = 0
		errors = []

		leave_type_to_deduct = "Cuti Tahunan"

		# total_overtime_hours_potential = 0.0 # Placeholder for future calculation
		total_leave_converted_days = 0

		for att in absent_attendances:
			try:
				leave_balance = (
					frappe.db.sql(
						"""
                    SELECT sum(leaves)
                    FROM `tabLeave Ledger Entry`
                    WHERE employee=%s AND leave_type=%s
                    """,
						(att.employee, leave_type_to_deduct),
						as_list=True,
					)[0][0]
					or 0
				)

				if leave_balance > 0:
					leave_app = frappe.new_doc("Leave Application")
					leave_app.employee = att.employee
					leave_app.leave_type = leave_type_to_deduct
					leave_app.from_date = att.attendance_date
					leave_app.to_date = att.attendance_date
					leave_app.half_day = 0
					leave_app.description = f"Dibuat otomatis oleh Sistem Validasi Payroll pada {nowdate()} untuk absensi pada {att.attendance_date}"
					leave_app.docstatus = 1
					leave_app.insert(ignore_permissions=True)

					frappe.db.set_value("Attendance", att.name, "status", "On Leave")
					converted_count += 1
					total_leave_converted_days += 1
				else:
					lwp_count += 1

			except Exception as e:
				errors.append(f"Error pada karyawan {att.employee} (Absensi {att.attendance_date}): {e!s}")
				frappe.log_error(
					frappe.get_traceback(),
					f"Gagal memproses absensi untuk {att.employee} pada {att.attendance_date}",
				)

		frappe.db.commit()

		summary_html = f"""
            <h4>Proses Validasi Absensi Selesai</h4>
            <ul>
                <li>Data Absensi & Pengajuan Cuti Sebelumnya Dihapus:
                    <ul>
                        <li>Absensi: <strong>{clear_counts['attendance']}</strong> record</li>
                        <li>Pengajuan Cuti: <strong>{clear_counts['leave_application']}</strong> record</li>
                    </ul>
                </li>
                <hr>
                <li>Total Karyawan Aktif Diproses: <strong>{total_active_employees}</strong></li>
                <li>Jumlah Hari dalam Periode: <strong>{total_days_in_period}</strong> hari</li>
                <li>Jumlah Hari Kerja Unik dalam Periode: <strong>{period_working_days_count}</strong> hari</li>
                <li>Jumlah Hari Libur Unik dalam Periode: <strong>{period_holiday_days_count}</strong> hari</li>
                <li>Karyawan dengan Shift Terdaftar: <strong>{len(employees_on_shift_in_period)}</strong> orang</li>
                <li>Karyawan Non-Shift Terdaftar: <strong>{len(employees_without_shift_in_period - employees_on_shift_in_period)}</strong> orang</li>
                <hr>
                <li>Absensi Implisit Dibuat: <strong>{created_implicit_absent_count}</strong> record</li>
                <li>Absensi Dikonversi menjadi Cuti: <strong>{converted_count}</strong> hari</li>
                <li>Absensi sebagai LWP: <strong>{lwp_count}</strong> hari</li>
                <li>Total Absensi Diproses: <strong>{len(absent_attendances)}</strong> record</li>
                <li>Total Cuti yang Dikonversi: <strong>{total_leave_converted_days}</strong> hari</li>
                <li>Estimasi Potensi Lembur (akan dihitung terpisah): <strong>{total_potential_overtime_hours}</strong> jam</li>
            </ul>
        """
		if errors:
			summary_html += "<h5>Detail Error:</h5><pre>" + "\n".join(errors) + "</pre>"

		self.db_set("hasil_validasi", summary_html)

		return summary_html

	def _get_overtime_rates_config(self):
		"""
		Loads and validates Overtime Calculation configurations for different day types.
		Throws an error if any required schema is missing or incomplete.
		"""
		overtime_rates_config = {}
		schema_names = {
			"Hari Kerja": self.WEEKDAY_SCHEMA,
			"Akhir Pekan": self.WEEKEND_SCHEMA,
			"Hari Libur Nasional": self.HOLIDAY_SCHEMA,
		}

		for day_type, schema_name in schema_names.items():
			overtime_calc_docs = frappe.get_all(
				"Overtime Calculation",
				filters={"nama_skema": schema_name},
				fields=["name"],
				limit=1,
			)
			if not overtime_calc_docs:
				frappe.throw(
					f"DocType 'Overtime Calculation' tidak memiliki skema tarif lembur untuk '{schema_name}'. "
					"Harap siapkan data ini terlebih dahulu."
				)
			overtime_calc_doc_name = overtime_calc_docs[0].name

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

	def _calculate_tiered_overtime_pay(
		self,
		overtime_duration_hours,
		base_hourly_rate,
		rates_for_day_type,
	):
		"""
		Calculates overtime pay based on tiered rates for a specific day type.
		`rates_for_day_type` is a sorted list of {jam_ke_mulai, jam_ke_selesai, pengali_upah}.
		"""
		total_overtime_pay = 0.0
		remaining_duration_to_pay = flt(overtime_duration_hours)

		# Iterate through the actual overtime hours
		current_ot_hour_index = 0.0  # From 0.0 to overtime_duration_hours

		while remaining_duration_to_pay > 0.001:  # Use small epsilon for float comparison
			# Determine the current hour being processed (1st, 2nd, 3rd, etc.)
			current_tier_hour_num = int(current_ot_hour_index) + 1  # 1st hour, 2nd hour, etc.

			# Find the rate for this specific hour
			applicable_multiplier = 1.0  # Default if no tier matches (should log a warning)
			found_tier = False
			for rate_tier in rates_for_day_type:
				if rate_tier.jam_ke_mulai <= current_tier_hour_num <= rate_tier.jam_ke_selesai:
					applicable_multiplier = rate_tier.pengali_upah
					found_tier = True
					break

			if not found_tier:
				# If no specific rate is defined for higher hours, use 1x multiplier and log a warning
				frappe.log_error(
					message=f"No overtime rate found for hour {current_tier_hour_num} and beyond. Defaulting to 1.0x. "
					f"Overtime duration: {overtime_duration_hours:.2f} hrs. Defined tiers might be insufficient.",
					title="Overtime Calculation Warning",
				)
				# We still want to pay for this duration, so applicable_multiplier remains 1.0

			# Calculate how much duration will be paid in this segment (up to next full hour, or remaining duration)
			duration_in_current_segment = min(
				remaining_duration_to_pay, flt(int(current_ot_hour_index) + 1) - current_ot_hour_index
			)

			total_overtime_pay += duration_in_current_segment * base_hourly_rate * applicable_multiplier
			remaining_duration_to_pay -= duration_in_current_segment
			current_ot_hour_index += duration_in_current_segment  # Advance the hour index

		return total_overtime_pay

	@frappe.whitelist()
	def get_overtime_report_data(self):
		"""
		Generates an HTML report for overtime data.
		It uses approved Overtime Planning details and tiered rates from Overtime Calculation DocTypes.
		"""
		if not self.start_date or not self.end_date:
			frappe.throw("Harap tentukan Start Date dan End Date terlebih dahulu.")

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		report_html = "<h4>Laporan Lembur</h4>"

		# Load Overtime Calculation rates and validate them
		try:
			overtime_rates_config = self._get_overtime_rates_config()
		except Exception as e:
			frappe.throw(f"Gagal memuat konfigurasi tarif lembur: {e!s}")

		overtime_plans_detail = frappe.get_all(
			"Overtime Planning Detail",
			filters=[
				["docstatus", "=", 1],
				["parent.overtime_date", ">=", start_date],
				["parent.overtime_date", "<=", end_date],
			],
			fields=[
				"name",
				"parent",
				"employee",
				"parent.overtime_date as overtime_date",
				"start_time",
				"end_time",
			],
			order_by="modified DESC",
		)

		if overtime_plans_detail:
			overtime_data_by_employee = {}
			company_holiday_cache = {}
			employee_shift_cache = {}
			hr_settings = frappe.get_single("HR Settings")
			standard_working_hours = hr_settings.standard_working_hours or 8  # Default 8 hours

			if not standard_working_hours or standard_working_hours == 0:
				frappe.throw(
					"'Standard Working Hours' tidak diatur di HR Settings atau bernilai nol. "
					"Harap atur untuk menghitung upah lembur."
				)

			for op_detail in overtime_plans_detail:
				employee_name = op_detail.employee
				overtime_date = op_detail.overtime_date
				start_time_str = op_detail.start_time
				end_time_str = op_detail.end_time

				# Convert to datetime objects for calculation
				start_dt = get_datetime(f"{overtime_date} {start_time_str}")
				end_dt = get_datetime(f"{overtime_date} {end_time_str}")

				# Handle overnight overtime (if end_time is next day)
				if end_dt < start_dt:
					end_dt = add_days(end_dt, 1)

				time_diff = end_dt - start_dt
				overtime_duration_hours = time_diff.total_seconds() / 3600

				# Determine day type for rate factor
				employee_doc_for_ot = frappe.get_cached_doc("Employee", employee_name)
				_, _, is_holiday, is_weekend = self._is_expected_to_work_on_day(
					employee_doc_for_ot, overtime_date, company_holiday_cache, employee_shift_cache
				)

				day_type_string = "Hari Kerja"
				if is_holiday:
					day_type_string = "Hari Libur Nasional"
				elif is_weekend:
					day_type_string = "Akhir Pekan"

				rates_for_day_type = overtime_rates_config.get(day_type_string)
				if (
					not rates_for_day_type
				):  # Should not happen if _get_overtime_rates_config validated correctly
					frappe.throw(
						f"Internal Error: Tarif lembur tidak ditemukan untuk jenis hari '{day_type_string}'."
					)

				# Get base hourly rate
				base_salary = (
					frappe.db.get_value(
						"Salary Structure Assignment",
						{"employee": employee_name, "docstatus": 1, "from_date": ["<=", overtime_date]},
						"base",
						order_by="from_date DESC",
					)
					or 0
				)

				base_hourly_rate = flt(base_salary) / (
					flt(standard_working_hours) * 22
				)  # Assuming 22 working days per month

				# Calculate tiered overtime pay
				estimated_overtime_pay = self._calculate_tiered_overtime_pay(
					overtime_duration_hours, base_hourly_rate, rates_for_day_type
				)

				if employee_name not in overtime_data_by_employee:
					overtime_data_by_employee[employee_name] = {
						"total_hours": 0.0,
						"total_pay": 0.0,
						"details": [],
					}
				overtime_data_by_employee[employee_name]["total_hours"] += overtime_duration_hours
				overtime_data_by_employee[employee_name]["total_pay"] += estimated_overtime_pay
				overtime_data_by_employee[employee_name]["details"].append(
					{
						"overtime_date": overtime_date,
						"start_time": start_time_str,
						"end_time": end_time_str,
						"duration": f"{overtime_duration_hours:.2f} jam",
						"day_type": day_type_string,
						"base_hourly_rate": f"Rp {base_hourly_rate:,.2f}",
						"estimated_pay": f"Rp {estimated_overtime_pay:,.2f}",
						"overtime_planning_doc": op_detail.parent,  # Link to actual Overtime Planning doc
					}
				)

			report_html += "<p><b>Catatan:</b> Perhitungan menggunakan tarif bertingkat dari DocType 'Overtime Calculation' dan gaji pokok bulanan dibagi jam kerja standar HR Settings (diasumsikan 22 hari kerja/bulan).</p>"
			report_html += "<table class='table table-bordered'><thead><tr><th>Employee</th><th>Tanggal</th><th>Mulai</th><th>Selesai</th><th>Durasi</th><th>Jenis Hari</th><th>Upah/Jam Dasar</th><th>Estimasi Upah</th><th>Overtime Planning</th></tr></thead><tbody>"

			# Sort employees by name for consistent report order
			sorted_employees = sorted(overtime_data_by_employee.keys())

			for emp in sorted_employees:
				data = overtime_data_by_employee[emp]
				for detail in data["details"]:
					report_html += f"<tr><td>{emp}</td><td>{detail['overtime_date']}</td><td>{detail['start_time']}</td><td>{detail['end_time']}</td><td>{detail['duration']}</td><td>{detail['day_type']}</td><td>{detail['base_hourly_rate']}</td><td>{detail['estimated_pay']}</td><td><a href='/app/Overtime Planning/{detail['overtime_planning_doc']}'>{detail['overtime_planning_doc']}</a></td></tr>"

				# Add total row for each employee
				report_html += f"<tr style=\"font-weight: bold;\"><td colspan=\"5\">Total {emp}</td><td></td><td>{data['total_hours']:.2f} jam</td><td>Rp {data['total_pay']:,.2f}</td><td></td></tr>"

			report_html += "</tbody></table>"
			# Final Totals
			total_all_employees_hours = sum(
				data["total_hours"] for data in overtime_data_by_employee.values()
			)
			total_all_employees_pay = sum(data["total_pay"] for data in overtime_data_by_employee.values())
			report_html += f'<h5 style="margin-top: 20px;">Total Keseluruhan Lembur: {total_all_employees_hours:.2f} jam, Total Estimasi Upah: Rp {total_all_employees_pay:,.2f}</h5>'

		else:
			report_html += "<p>Tidak ditemukan data Overtime Planning yang disubmit pada periode ini.</p>"

		self.db_set("hasil_validasi", report_html)
		frappe.db.commit()
		return report_html

	@frappe.whitelist()
	def get_leave_report_data(self):
		"""
		Generates an HTML report for leave data including Leave Applications and Leave Ledger Entries.
		"""
		if not self.start_date or not self.end_date:
			frappe.throw("Harap tentukan Start Date dan End Date terlebih dahulu.")

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		report_html = "<h4>Laporan Cuti</h4>"

		# Fetch Leave Applications for the period
		leave_applications = frappe.get_all(
			"Leave Application",
			filters={
				"from_date": ["<=", end_date],
				"to_date": [">=", start_date],
				"docstatus": 1,  # Hanya yang disubmit
			},
			fields=["name", "employee", "leave_type", "from_date", "to_date", "status"],
		)

		if leave_applications:
			report_html += "<h5>Pengajuan Cuti (Leave Applications)</h5>"
			report_html += "<table class='table table-bordered'><thead><tr><th>No.</th><th>Employee</th><th>Leave Type</th><th>From Date</th><th>To Date</th><th>Status</th></tr></thead><tbody>"
			for la in leave_applications:
				report_html += f"<tr><td>{la.name}</td><td>{la.employee}</td><td>{la.leave_type}</td><td>{la.from_date}</td><td>{la.to_date}</td><td>{la.status}</td></tr>"
			report_html += "</tbody></table>"
		else:
			report_html += "<p>Tidak ditemukan Pengajuan Cuti pada periode ini.</p>"

		# Fetch Leave Ledger Entries for the period (summary per employee)
		# This query might be heavy, consider optimizing if performance is an issue with many employees/entries.
		leave_ledger_entries = frappe.db.sql(
			"""
            SELECT
                lle.employee,
                lle.leave_type,
                SUM(lle.leaves) AS total_leaves_change
            FROM
                `tabLeave Ledger Entry` lle
            WHERE
                lle.transaction_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY
                lle.employee, lle.leave_type
            ORDER BY
                lle.employee, lle.leave_type
            """,
			{"start_date": start_date, "end_date": end_date},
			as_dict=True,
		)

		if leave_ledger_entries:
			report_html += "<h5>Pergerakan Saldo Cuti (Leave Ledger Summary)</h5>"
			report_html += "<table class='table table-bordered'><thead><tr><th>Employee</th><th>Leave Type</th><th>Total Leaves Change</th></tr></thead><tbody>"
			for lle in leave_ledger_entries:
				report_html += f"<tr><td>{lle.employee}</td><td>{lle.leave_type}</td><td>{lle.total_leaves_change}</td></tr>"
			report_html += "</tbody></table>"
		else:
			report_html += "<p>Tidak ditemukan Pergerakan Saldo Cuti pada periode ini.</p>"

		self.db_set("hasil_validasi", report_html)
		frappe.db.commit()
		return report_html
