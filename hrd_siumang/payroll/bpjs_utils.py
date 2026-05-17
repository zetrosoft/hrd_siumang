import frappe

@frappe.whitelist()
def get_employee_bpjs_salary(employee):
    try:
        # Get active Salary Structure Assignment
        ssa = frappe.get_doc("Salary Structure Assignment", {"employee": employee, "docstatus": 1})
        if not ssa:
            return 0
        
        base_amount = ssa.base
        
        tunjangan_tetap = 0
        # Check Employee Allowance Data
        if frappe.db.exists("Employee Allowance Data", {"employee": employee}):
            ea_doc = frappe.get_doc("Employee Allowance Data", {"employee": employee})
            tunjangan_jabatan = ea_doc.tunjangan_jabatan or 0
            tunjangan_komunikasi = ea_doc.tunjangan_komunikasi or 0
            tunjangan_tetap = tunjangan_jabatan + tunjangan_komunikasi
            
        return base_amount + tunjangan_tetap
    except Exception as e:
        frappe.log_error(f"Error getting BPJS salary for {employee}: {str(e)}")
        return 0
