import frappe
import json
from frappe.utils import get_last_day

def run_full_payroll_simulation(employee_id="HR-EMP-00004", month="04", year="2026"):
    try:
        start_date = f"{year}-{month}-01"
        end_date = get_last_day(start_date)
        
        # 1. Inisialisasi Salary Slip Baru dari Awal
        doc = frappe.new_doc("Salary Slip")
        doc.employee = employee_id
        doc.start_date = start_date
        doc.end_date = end_date
        doc.posting_date = end_date
        doc.company = frappe.db.get_value("Employee", employee_id, "company")
        doc.payroll_frequency = "Monthly"
        
        # 2. Lakukan Insert (Mensimulasikan siklus penuh: koleksi absensi, struktur, kalkulasi net pay, memicu before_save)
        # Kita matikan error jika ada mandat yang tidak valid agar simulasi tetap jalan
        doc.flags.ignore_validate = False
        doc.insert(ignore_permissions=True)
        
        # 3. Kumpulkan Output setelah siklus lengkap dijalankan
        ea_data = frappe.db.get_value("Employee Allowance Data", {"employee": employee_id}, 
            ["tunjangan_jabatan", "tunjangan_komunikasi", "tunjangan_transport", "tunjangan_makan", "manual_payroll_denominator"], as_dict=1) or {}
        
        denominator = ea_data.get("manual_payroll_denominator") or 21
        
        earnings_list = {e.salary_component: e.amount for e in doc.earnings if e.amount > 0}
        deductions_list = {d.salary_component: d.amount for d in doc.deductions if d.amount > 0}
        
        # Validasi Formula
        target_components = ["Gaji Pokok", "Tj. Jabatan", "Tj. Komunikasi", "Tj. Transport", "Tj. Makan", "Tj. Lain"]
        total_earnings_base = sum([amt for name, amt in earnings_list.items() if any(comp in name for comp in target_components)])
        
        expected_absensi = round((total_earnings_base / denominator) * (doc.absent_days + doc.leave_without_pay)) if denominator > 0 else 0
        
        results = {
            "step": "Full Simulation (Created from Scratch via doc.insert)",
            "employee": doc.employee_name,
            "period": f"{start_date} to {end_date}",
            "attendance_collected_from_db": {
                "total_working_days": doc.total_working_days,
                "absent_days": doc.absent_days,
                "leave_without_pay": doc.leave_without_pay,
                "payment_days": doc.payment_days,
                "total_unpaid_days": doc.absent_days + doc.leave_without_pay,
                "denominator_standard": denominator
            },
            "earnings_calculated": earnings_list,
            "deductions_calculated": deductions_list,
            "verification": {
                "base_for_deduction": total_earnings_base,
                "formula_used": f"({total_earnings_base} / {denominator}) * {doc.absent_days + doc.leave_without_pay}",
                "expected_deduction_amount": expected_absensi,
                "actual_deduction_on_slip": deductions_list.get("Absensi", 0)
            },
            "status": "BERHASIL (MATCH)" if expected_absensi == deductions_list.get("Absensi", 0) else "GAGAL (Nilai tidak cocok)"
        }
        
        # 4. Rollback database agar slip gaji tidak benar-benar tersimpan
        frappe.db.rollback()
        
        return json.dumps(results, indent=4)

    except Exception as e:
        frappe.db.rollback()
        import traceback
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})
