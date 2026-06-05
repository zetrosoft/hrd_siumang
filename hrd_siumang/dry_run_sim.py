import frappe
from hrd_siumang.payroll.salary_slip_events import calculate_payroll_components
import json

def dry_run():
    employee = "HR-EMP-00013"
    company = "PT. SIUMANG TEMAN SUKSES"
    salary_structure = "Struktur Gaji - Permanen"
    start_date = "2026-06-01"
    end_date = "2026-06-30"

    print(f"--- Dry Run Payroll: {employee} ({start_date} to {end_date}) ---")

    # Create in-memory Salary Slip
    doc = frappe.new_doc("Salary Slip")
    doc.employee = employee
    doc.company = company
    doc.salary_structure = salary_structure
    doc.start_date = start_date
    doc.end_date = end_date
    doc.docstatus = 0 # Draft mode for calculation

    # Simulation: Clear shift to test hard-block
    # frappe.db.set_value("Employee", employee, "default_shift", None)
    # frappe.db.sql(f"update `tabShift Assignment` set status = 'Inactive' where employee = '{employee}'")
    
    # BPJS Setting (Trigger auto-fill if empty for simulation)
    bpjs_setting = frappe.get_doc("BPJS Setting", "BPJS Setting")
    bpjs_setting.validate()
    
    try:
        # Run calculation
        calculate_payroll_components(doc, "before_save")
    except frappe.ValidationError as e:
        print(f"\n[EXPECTED ERROR CATCHED]\n{e}")
        return
    except Exception as e:
        print(f"\n[ERROR]\n{e}")
        return

    # Result Summary
    print(f"Employee Name: {doc.employee_name}")
    print(f"Salary Structure: {doc.salary_structure}")
    print("\n[Earnings]")
    for e in doc.earnings:
        if e.amount > 0:
            print(f"- {e.salary_component}: {e.amount:,.2f}")
    
    print("\n[Deductions]")
    for d in doc.deductions:
        if d.amount > 0:
            print(f"- {d.salary_component}: {d.amount:,.2f}")

    print("\n--- Totals ---")
    print(f"Gross Pay: {doc.gross_pay:,.2f}")
    print(f"Total Deduction: {doc.total_deduction:,.2f}")
    print(f"Net Pay: {doc.net_pay:,.2f}")

if __name__ == "__main__":
    frappe.init(site="siumang")
    frappe.connect()
    try:
        dry_run()
    finally:
        frappe.destroy()
