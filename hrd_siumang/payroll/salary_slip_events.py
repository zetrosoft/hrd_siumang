import frappe
from frappe import _
from frappe.query_builder import Order
from datetime import timedelta
from frappe.utils import getdate, add_days, date_diff, get_time, time_diff_in_hours
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

from hrd_siumang.payroll.payroll_utils import calculate_overtime, calculate_pph21, get_payroll_denominator


def _get_unplanned_overtime(employee, start_date, end_date, shift_type_name, holiday_list):
	"""
	Mendeteksi kelebihan jam kerja atau kehadiran di hari libur yang belum ada Overtime Planning-nya.
	"""
	unplanned_list = []
	if not shift_type_name:
		return unplanned_list

	shift_type = frappe.get_doc("Shift Type", shift_type_name)
	shift_end_time = shift_type.end_time
	
	# Get all checkins for the period
	checkins = frappe.get_all("Employee Checkin", filters={
		"employee": employee,
		"time": ["between", [start_date, f"{end_date} 23:59:59"]]
	}, fields=["time", "log_type"], order_by="time asc")

	# Get all approved overtime for the period
	approved_ot = frappe.db.sql(f"""
		SELECT parent.overtime_date 
		FROM `tabOvertime Planning Detail` detail
		JOIN `tabOvertime Planning` parent ON detail.parent = parent.name
		WHERE detail.employee = '{employee}' AND parent.docstatus = 1 
		AND parent.overtime_date BETWEEN '{start_date}' AND '{end_date}'
	""", as_dict=True)
	approved_ot_dates = {getdate(d.overtime_date) for d in approved_ot}

	# Process checkins by date
	daily_logs = {}
	for c in checkins:
		d = getdate(c.time)
		if d not in daily_logs:
			daily_logs[d] = []
		daily_logs[d].append(c)

	for log_date, logs in daily_logs.items():
		if log_date in approved_ot_dates:
			continue
		
		is_hol = is_holiday(holiday_list, log_date)
		
		# Kasus Hari Libur: Ada fingerprint tapi tidak ada pengajuan OT
		if is_hol:
			unplanned_list.append({
				"date": log_date,
				"reason": "Masuk di Hari Libur tanpa pengajuan OT"
			})
			continue

		# Kasus Hari Kerja: Cek kelebihan jam (Check-out > Shift End)
		outs = [l.time for l in logs if l.log_type == "OUT"]
		if outs:
			last_out = max(outs)
			out_time = last_out.time()
			
			# Convert shift_end_time (timedelta) to time object for comparison
			shift_end_obj = (timedelta(0, 0) + shift_end_time)
			last_out_delta = timedelta(hours=out_time.hour, minutes=out_time.minute, seconds=out_time.second)
			
			# Jika telat pulang lebih dari 1 jam (asumsi lembur minimal 1 jam)
			diff_hours = (last_out_delta - shift_end_obj).total_seconds() / 3600
			if diff_hours >= 1.0:
				unplanned_list.append({
					"date": log_date,
					"reason": f"Kelebihan {round(diff_hours, 1)} jam kerja tanpa pengajuan OT"
				})

	return unplanned_list



def _get_unmarked_and_absent_days(employee, start_date, end_date, holiday_list):
	"""
	Menghitung hari mangkir (unmarked) atau absen eksplisit pada hari kerja.
	Hari yang tidak ada fingerprint dan tidak ada cuti dihitung sebagai potongan.
	"""
	total_unpaid = 0
	curr_date = getdate(start_date)
	end_date_obj = getdate(end_date)
	
	# Cache attendance for the period
	attendance_records = frappe.get_all("Attendance", filters={
		"employee": employee,
		"attendance_date": ["between", [start_date, end_date]],
		"docstatus": 1
	}, fields=["attendance_date", "status"])
	attendance_map = {getdate(d.attendance_date): d.status for d in attendance_records}
	
	# Cache approved leaves
	leave_applications = frappe.get_all("Leave Application", filters={
		"employee": employee,
		"status": "Approved",
		"docstatus": 1,
		"from_date": ["<=", end_date],
		"to_date": [">=", start_date]
	}, fields=["from_date", "to_date"])
	
	approved_leave_dates = set()
	for leave in leave_applications:
		d = getdate(max(getdate(leave.from_date), getdate(start_date)))
		limit = getdate(min(getdate(leave.to_date), getdate(end_date)))
		while d <= limit:
			approved_leave_dates.add(d)
			d = getdate(add_days(d, 1))

	# Iterate every day
	while curr_date <= end_date_obj:
		# Jika bukan hari libur
		if not is_holiday(holiday_list, curr_date):
			status = attendance_map.get(curr_date)
			
			# Jika tidak ada record attendance DAN tidak ada cuti disetujui -> Unmarked (Mangkir)
			if not status and curr_date not in approved_leave_dates:
				total_unpaid += 1
			# Jika statusnya eksplisit Absent
			elif status == "Absent":
				total_unpaid += 1
				
		curr_date = getdate(add_days(curr_date, 1))
		
	return total_unpaid



def _calculate_borongan_for_employee(employee, start_date, end_date):
	"""Helper function to calculate total piecework earnings for a single employee."""
	total_earnings = 0

	# --- 1. Get Individual Earnings ---
	individual_earnings = frappe.db.sql(
		"""
		SELECT SUM(d.total_harga_item)
		FROM `tabDetail Hasil Borongan` d
		JOIN `tabInput Hasil Borongan` p ON d.parent = p.name
		WHERE d.tipe_penerima_tugas = 'Individu'
		AND d.karyawan = %(employee)s
		AND p.docstatus = 1
		AND p.tanggal BETWEEN %(start_date)s AND %(end_date)s
	""",
		{"employee": employee, "start_date": start_date, "end_date": end_date},
	)
	if individual_earnings and individual_earnings[0][0]:
		total_earnings += individual_earnings[0][0]

	# --- 2. Get Team Earnings ---
	member_of_teams = frappe.get_all("Anggota Tim Borongan", filters={"karyawan": employee}, pluck="parent")
	if not member_of_teams:
		return total_earnings

	team_based_work = frappe.get_all(
		"Detail Hasil Borongan",
		fields=["parent", "karyawan", "total_harga_item"],
		filters={
			"tipe_penerima_tugas": "Tim",
			"karyawan": ["in", member_of_teams],
			"parenttype": "Input Hasil Borongan",
		},
	)

	if not team_based_work:
		return total_earnings

	parent_docs = frappe.get_all(
		"Input Hasil Borongan",
		filters={
			"name": ("in", [d.parent for d in team_based_work]),
			"docstatus": 1,
			"tanggal": ("between", [start_date, end_date]),
		},
		fields=["name", "tanggal"],
	)
	valid_parents = {doc.name: doc.tanggal for doc in parent_docs}

	team_member_counts = {}
	for team_name in member_of_teams:
		count = frappe.db.count("Anggota Tim Borongan", {"parent": team_name, "parenttype": "Tim Borongan"})
		team_member_counts[team_name] = count if count > 0 else 1

	for work in team_based_work:
		if work.parent in valid_parents:
			team_name = work.karyawan
			num_members = team_member_counts.get(team_name, 1)
			employee_share = work.total_harga_item / num_members
			total_earnings += employee_share

	return total_earnings


def calculate_payroll_components(doc, method):
	"""
	DocEvent for Salary Slip before_save.
	"""
	if getattr(doc, "custom_is_incentive_slip", None) or doc.docstatus > 0:
		return

	if doc.payroll_entry:
		is_incentive_pe = frappe.db.get_value("Payroll Entry", doc.payroll_entry, "custom_incentive_employee_incentive")
		if is_incentive_pe:
			return

	if not doc.salary_structure:
		return

	# --- Common Variables ---
	employee_id = doc.employee
	start_date = doc.start_date
	end_date = doc.end_date
	
	# Determine Denominator (21 or 25)
	denominator = get_payroll_denominator(employee_id)
	
	# --- VALIDASI SHIFT TYPE & HOLIDAY LIST ---
	shift_type = frappe.get_value("Shift Assignment", 
		{"employee": employee_id, "docstatus": 1, "status": "Active", "start_date": ("<=", end_date)}, 
		"shift_type")
	if not shift_type:
		shift_type = frappe.db.get_value("Employee", employee_id, "default_shift")
	
	holiday_list = frappe.get_value("Shift Type", shift_type, "holiday_list") if shift_type else None
	if not holiday_list:
		holiday_list = frappe.db.get_value("Employee", employee_id, "holiday_list")
	
	# Hitung hari mangkir (termasuk unmarked attendance)
	absent_days = _get_unmarked_and_absent_days(employee_id, start_date, end_date, holiday_list)
	
	# --- VALIDASI OVERTIME TAK TERENCANA ---
	unplanned_ot = _get_unplanned_overtime(employee_id, start_date, end_date, shift_type, holiday_list)
	if unplanned_ot:
		ot_msg = _("Ditemukan kelebihan jam kerja/kehadiran hari libur yang {0}:").format(frappe.bold("TIDAK MEMILIKI pengajuan Overtime Planning"))
		ot_list_html = "<ul>"
		for item in unplanned_ot:
			ot_list_html += f"<li><b>{item['date']}</b>: {item['reason']}</li>"
		ot_list_html += "</ul>"
		ot_msg += ot_list_html
		ot_msg += _("<br>Gaji lembur untuk tanggal-tanggal di atas {0}. Mohon lengkapi pengajuan OT jika ingin dibayarkan.").format(frappe.bold("TIDAK AKAN DIHITUNG"))
		
		frappe.msgprint(ot_msg, title=_("Lembur Tak Terencana Terdeteksi"), indicator="orange")

	if not shift_type:
		msg = _("Karyawan {0} tidak dapat diproses karena tidak memiliki Shift Type aktif (Default maupun Assignment) untuk periode ini.").format(frappe.bold(doc.employee_name or employee_id))
		msg += f"<br><br><b>Detail Ketidakhadiran:</b><br>- Perkiraan mangkir (tanpa fingerprint/cuti): {absent_days} hari."
		frappe.throw(msg, title=_("Shift Type Belum Diatur"))

	# BPJS Base Calculation
	# Fetch base from Salary Structure Assignment
	assignment = frappe.db.get_value(
		"Salary Structure Assignment",
		{
			"employee": employee_id,
			"salary_structure": doc.salary_structure,
			"from_date": ("<=", start_date),
			"docstatus": 1,
		},
		"base",
		order_by="from_date desc"
	)
	base_amount = assignment or getattr(doc, "base", 0) or 0
	
	# Fallback to Employee CTC if base is still 0
	if not base_amount:
		base_amount = frappe.db.get_value("Employee", employee_id, "ctc") or 0
	
	ea_doc = None
	tunjangan_tetap = 0
	if frappe.db.exists("Employee Allowance Data", {"employee": employee_id}):
		ea_doc = frappe.get_doc("Employee Allowance Data", {"employee": employee_id})
		
		# Dinamis: Cek checkbox Is Fixed untuk setiap komponen
		if ea_doc.is_tunjangan_jabatan_fixed:
			tunjangan_tetap += (ea_doc.tunjangan_jabatan or 0)
		if ea_doc.is_tunjangan_komunikasi_fixed:
			tunjangan_tetap += (ea_doc.tunjangan_komunikasi or 0)
		if getattr(ea_doc, "is_tunjangan_transport_fixed", False):
			tunjangan_tetap += (ea_doc.tunjangan_transport or 0)
		if getattr(ea_doc, "is_tunjangan_makan_fixed", False):
			tunjangan_tetap += (ea_doc.tunjangan_makan or 0)
		if getattr(ea_doc, "is_tunjangan_lain_fixed", False):
			tunjangan_tetap += (ea_doc.tunjangan_lain or 0)
	
	bpjs_base = base_amount + tunjangan_tetap

	# --- 1. Handle Unpaid Leaves & Cuti Bersama Logic ---
	# Get Attendance and Leave records
	unpaid_days = 0
	
	# ST: Sakit Tanpa Surat (Always Unpaid)
	st_days = frappe.db.count("Leave Application", {
		"employee": employee_id,
		"leave_type": "Sakit (Tanpa Surat)",
		"status": "Approved",
		"from_date": ["<=", end_date],
		"to_date": [">=", start_date],
		"docstatus": 1
	})
	
	# CB: Cuti Bersama (Check balance)
	# This is a simplification: if jatah is 0, it counts as unpaid
	# In real ERPNext, it's better to check Leave Ledger, but here we follow the "potong upah" requirement
	# We'll check if Leave Application "Cuti Bersama" exists for this period
	cb_applications = frappe.get_all("Leave Application", filters={
		"employee": employee_id,
		"leave_type": "Cuti Bersama",
		"status": "Approved",
		"from_date": ["<=", end_date],
		"to_date": [">=", start_date],
		"docstatus": 1
	}, fields=["total_leave_days"])
	
	cb_unpaid_days = 0
	for cb in cb_applications:
		# Logic: if jatah is negative or 0 (simulated by a custom check or just policy)
		# For this implementation, we'll assume CB is unpaid if it's explicitly marked as unpaid 
		# OR we can check remaining leave balance of 'Cuti Tahunan'
		annual_leave_balance = frappe.db.get_value("Leave Allocation", 
			{"employee": employee_id, "leave_type": "Cuti Tahunan", "docstatus": 1}, 
			"unused_leaves") or 0
		
		if annual_leave_balance <= 0:
			cb_unpaid_days += cb.total_leave_days

	unpaid_days = st_days + cb_unpaid_days + absent_days

	# --- 2. Calculation Logic for Different Structures ---
	new_earnings = []
	new_deductions = []
	earnings_map = {}
	deductions_map = {}

	# BPJS Setting Logic
	bpjs_setting = frappe.get_doc("BPJS Setting", "BPJS Setting") if frappe.db.exists("BPJS Setting", "BPJS Setting") else None
	if bpjs_setting:
		bpjs_setting.validate() # Trigger auto-fill if empty
	
	include_bpjs_tk = True
	include_bpjs_kes = True
	bpjs_base_tk = bpjs_base
	bpjs_base_kes = bpjs_base

	# --- Tenure Based BPJS Eligibility (Migrated from Server Script) ---
	date_of_joining = frappe.db.get_value("Employee", employee_id, "date_of_joining")
	health_insurance_no = frappe.db.get_value("Employee", employee_id, "health_insurance_no")
	
	is_eligible_bpjs = True
	if date_of_joining:
		from frappe.utils import date_diff
		# Check if tenure > 90 days (approx 3 months)
		diff_days = date_diff(end_date, date_of_joining)
		if diff_days <= 90 or not health_insurance_no:
			is_eligible_bpjs = False
			include_bpjs_tk = False
			include_bpjs_kes = False

	if bpjs_setting and is_eligible_bpjs:
		if hasattr(bpjs_setting, "pengecualian_gaji"):
			for exc in bpjs_setting.pengecualian_gaji:
				if exc.employee == employee_id and exc.reported_salary:
					bpjs_base_tk = exc.reported_salary
					bpjs_base_kes = exc.reported_salary
					break
		if hasattr(bpjs_setting, "pengecualian_komponen"):
			for exc in bpjs_setting.pengecualian_komponen:
				if exc.employee == employee_id:
					# Logika: Jika dicentang di UI (True), maka dikecualikan (False)
					include_bpjs_tk = not exc.include_bpjs_tk
					include_bpjs_kes = not exc.include_bpjs_kes
					break

	# Special Path for Harian
	if doc.salary_structure == "Struktur Gaji - Harian":
		total_borongan = _calculate_borongan_for_employee(employee_id, start_date, end_date)
		earnings_map["Gaji Pokok"] = total_borongan
		if total_borongan == 0:
			bpjs_base_tk = 0
			bpjs_base_kes = 0
	else:
		# Monthly Calculation
		earnings_map["Gaji Pokok"] = base_amount
		if ea_doc:
			# Hitung faktor kehadiran untuk pemotongan proporsional tunjangan tidak tetap
			# Gunakan doc.payment_days dari HRMS standar agar akurat 100% dengan UI
			# Jika payment_days = 0 (karyawan absen sebulan penuh), maka faktornya 0
			payment_days_hrms = getattr(doc, "payment_days", 0)
			
			# Pastikan payment_days tidak melebihi denominator (batas maksimal 1.0)
			payment_days_hrms = min(payment_days_hrms, denominator)
			attendance_factor = payment_days_hrms / denominator if denominator > 0 else 1

			tunjangan_list = [
				("Tj. Jabatan", ea_doc.tunjangan_jabatan, ea_doc.is_tunjangan_jabatan_fixed),
				("Tj. Komunikasi", ea_doc.tunjangan_komunikasi, ea_doc.is_tunjangan_komunikasi_fixed),
				("Tj. Transport", ea_doc.tunjangan_transport, getattr(ea_doc, "is_tunjangan_transport_fixed", False)),
				("Tj. Makan", ea_doc.tunjangan_makan, getattr(ea_doc, "is_tunjangan_makan_fixed", False)),
				("Tj. Lain", ea_doc.tunjangan_lain, getattr(ea_doc, "is_tunjangan_lain_fixed", False)),
			]

			# MODIFIKASI SIUMANG: Semua tunjangan dibayar 100%, potongan dikumpulkan di komponen Absensi
			# Logika Lama (Dinonaktifkan):
			# for nama_komponen, nominal, is_fixed in tunjangan_list:
			# 	nominal = nominal or 0
			# 	if is_fixed:
			# 		# Tunjangan Tetap masuk 100% (potongan dilakukan via komponen Absensi di Deductions)
			# 		earnings_map[nama_komponen] = nominal
			# 	else:
			# 		# Tunjangan Tidak Tetap (Variabel) dipotong secara proporsional sesuai hari hadir
			# 		earnings_map[nama_komponen] = round(nominal * attendance_factor)
			
			# Logika Baru:
			total_seluruh_tunjangan = 0
			for nama_komponen, nominal, is_fixed in tunjangan_list:
				nominal = nominal or 0
				earnings_map[nama_komponen] = nominal
				total_seluruh_tunjangan += nominal
		
		# Apply Absent Deduction (The 21/25 logic)
		# Selaraskan juga perhitungan deduction dengan doc.absent_days + LWP dari UI
		total_absen_ui = getattr(doc, "absent_days", 0) + getattr(doc, "leave_without_pay", 0)
		
		# MODIFIKASI SIUMANG: Dasar potongan = Gaji Pokok + Semua Tunjangan
		# Logika Lama (Dinonaktifkan):
		# if total_absen_ui > 0:
		# 	deductions_map["Absensi"] = round((bpjs_base / denominator) * total_absen_ui)
		# else:
		# 	deductions_map["Absensi"] = 0

		# Logika Baru:
		base_potongan_absensi = base_amount + (total_seluruh_tunjangan if ea_doc else 0)
		if total_absen_ui > 0:
			deductions_map["Absensi"] = round((base_potongan_absensi / denominator) * total_absen_ui)
		else:
			deductions_map["Absensi"] = 0

	# BPJS Components
	bpjs_tk_map = {d.salary_component: d.percentage for d in bpjs_setting.komponen_bpjs_tk} if bpjs_setting else {}
	bpjs_kes_map = {d.salary_component: d.percentage for d in bpjs_setting.komponen_bpjs_kes} if bpjs_setting else {}

	if include_bpjs_tk:
		# Mapping standard keys to their actual names in BPJS Setting (even if renamed)
		tk_to_calculate = {
			"JHT Perusahaan": 3.7, 
			"JKK": 0.89, 
			"JKM": 0.3, 
			"JP Perusahaan": 2.0,
			"JHT Karyawan": 2.0, 
			"JP Karyawan": 1.0
		}
		
		for comp_key, default_pct in tk_to_calculate.items():
			# Find actual component name in map that starts with our key
			actual_comp_name = next((name for name in bpjs_tk_map if name.startswith(comp_key)), None)
			
			if actual_comp_name:
				percentage = bpjs_tk_map[actual_comp_name]
				amount = round(bpjs_base_tk * (percentage / 100))
				
				if "Perusahaan" in actual_comp_name or any(x in actual_comp_name for x in ["JKK", "JKM"]):
					earnings_map[actual_comp_name] = amount
					deductions_map[actual_comp_name] = amount
				else:
					deductions_map[actual_comp_name] = amount

	if include_bpjs_kes:
		# Process JKN Perusahaan
		jkn_p_name = next((name for name in bpjs_kes_map if "JKN Perusahaan" in name), None)
		if jkn_p_name:
			pct = bpjs_kes_map[jkn_p_name]
			amt = round(bpjs_base_kes * (pct / 100))
			earnings_map[jkn_p_name] = amt
			deductions_map[jkn_p_name] = amt
			
		# Process JKN Karyawan
		jkn_k_name = next((name for name in bpjs_kes_map if "JKN Karyawan" in name), None)
		if jkn_k_name:
			pct = bpjs_kes_map[jkn_k_name]
			amt = round(bpjs_base_kes * (pct / 100))
			deductions_map[jkn_k_name] = amt

	earnings_map["Overtime"] = calculate_overtime(doc)

	# Additional Salary integration
	additional_salaries = frappe.get_all("Additional Salary", filters={
		"employee": employee_id,
		"payroll_date": ["between", (start_date, end_date)],
		"docstatus": 1,
	}, fields=["salary_component", "amount", "type"])
	
	for ad_sal in additional_salaries:
		target_map = earnings_map if ad_sal.type == "Earning" else deductions_map
		target_map[ad_sal.salary_component] = target_map.get(ad_sal.salary_component, 0) + ad_sal.amount

	# Finalize Structure
	salary_structure_doc = frappe.get_doc("Salary Structure", doc.salary_structure)
	
	# PPh 21 Calculation
	doc.gross_pay = sum(earnings_map.values())
	deductions_map["Tax"] = calculate_pph21(doc)

	for comp_row in salary_structure_doc.earnings:
		amount = earnings_map.get(comp_row.salary_component, 0)
		new_earnings.append({"doctype": "Salary Detail", "salary_component": comp_row.salary_component, "amount": amount})

	for comp_row in salary_structure_doc.deductions:
		amount = deductions_map.get(comp_row.salary_component, 0)
		new_deductions.append({"doctype": "Salary Detail", "salary_component": comp_row.salary_component, "amount": amount})

	doc.set("earnings", new_earnings)
	doc.set("deductions", new_deductions)
	doc.gross_pay = sum(e.get("amount", 0) for e in new_earnings)
	doc.total_deduction = sum(d.get("amount", 0) for d in new_deductions)
	doc.net_pay = doc.gross_pay - doc.total_deduction

	# Prevent negative Net Pay by capping total deductions to gross pay
	if doc.net_pay < 0:
		doc.net_pay = 0
		# We must balance the equation: Gross - Deduction = Net (0)
		# So, Total Deduction must be exactly equal to Gross Pay
		adjustment_needed = doc.total_deduction - doc.gross_pay
		doc.total_deduction = doc.gross_pay
		
		# Adjust the "Absensi" row to absorb the difference so the breakdown remains logical
		for d in new_deductions:
			if d.get("salary_component") == "Absensi":
				d["amount"] -= adjustment_needed
				if d["amount"] < 0:
					d["amount"] = 0
				break
		doc.set("deductions", new_deductions)

