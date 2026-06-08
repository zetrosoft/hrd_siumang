import frappe
import json

def run_test(employee_id="HR-EMP-00153"):
    from hrd_siumang.payroll.salary_slip_events import calculate_payroll_components
    
    # Ambil slip terakhir sebagai sampel
    slip_name = frappe.db.get_value("Salary Slip", {"employee": employee_id}, "name", order_by="start_date desc")
    if not slip_name:
        print(f"Slip tidak ditemukan untuk {employee_id}")
        return

    doc = frappe.get_doc("Salary Slip", slip_name)
    
    # Jalankan logika baru
    calculate_payroll_components(doc, "before_save")
    
    results = {
        "employee": doc.employee_name,
        "base_pay": getattr(doc, "base", "N/A"),
        "earnings": {e.salary_component: e.amount for e in doc.earnings if e.amount > 0},
        "deductions": {d.salary_component: d.amount for d in doc.deductions if d.amount > 0},
        "gross": doc.gross_pay,
        "net": doc.net_pay
    }
    
    print(json.dumps(results, indent=4))
