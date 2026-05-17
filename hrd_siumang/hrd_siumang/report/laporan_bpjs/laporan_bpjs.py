import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {"label": _("ID Karyawan"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Nama Karyawan"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("Gaji Dilaporkan (Base BPJS)"), "fieldname": "reported_salary", "fieldtype": "Currency", "width": 180},
        {"label": _("JHT Perusahaan 3,7%"), "fieldname": "jht_company", "fieldtype": "Currency", "width": 150},
        {"label": _("JKK 0,89%"), "fieldname": "jkk", "fieldtype": "Currency", "width": 120},
        {"label": _("JKM 0,3%"), "fieldname": "jkm", "fieldtype": "Currency", "width": 120},
        {"label": _("JP Perusahaan 2%"), "fieldname": "jp_company", "fieldtype": "Currency", "width": 150},
        {"label": _("JKN Perusahaan 4%"), "fieldname": "jkn_company", "fieldtype": "Currency", "width": 150},
        {"label": _("JHT Karyawan 2%"), "fieldname": "jht_employee", "fieldtype": "Currency", "width": 150},
        {"label": _("JP Karyawan 1%"), "fieldname": "jp_employee", "fieldtype": "Currency", "width": 150},
        {"label": _("JKN Karyawan 1%"), "fieldname": "jkn_employee", "fieldtype": "Currency", "width": 150},
        {"label": _("Total BPJS Perusahaan"), "fieldname": "total_company", "fieldtype": "Currency", "width": 180},
        {"label": _("Total Potongan Karyawan"), "fieldname": "total_employee", "fieldtype": "Currency", "width": 180},
        {"label": _("Total BPJS Keseluruhan"), "fieldname": "total_all", "fieldtype": "Currency", "width": 180}
    ]

def get_data(filters):
    conditions = "docstatus = 1"
    
    if filters.get("month"):
        conditions += f" AND MONTH(start_date) = '{filters.get('month')}'"
    if filters.get("year"):
        conditions += f" AND YEAR(start_date) = '{filters.get('year')}'"
    if filters.get("employee"):
        conditions += f" AND employee = '{filters.get('employee')}'"
        
    slips = frappe.db.sql(f"""
        SELECT 
            name, employee, employee_name
        FROM 
            `tabSalary Slip`
        WHERE 
            {conditions}
    """, as_dict=1)
    
    data = []
    
    for slip in slips:
        details = frappe.get_all("Salary Detail", 
            filters={"parent": slip.name, "parenttype": "Salary Slip"},
            fields=["salary_component", "amount", "parentfield"]
        )
        
        row = {
            "employee": slip.employee,
            "employee_name": slip.employee_name,
            "reported_salary": 0,
            "jht_company": 0,
            "jkk": 0,
            "jkm": 0,
            "jp_company": 0,
            "jkn_company": 0,
            "jht_employee": 0,
            "jp_employee": 0,
            "jkn_employee": 0,
            "total_company": 0,
            "total_employee": 0,
            "total_all": 0
        }
        
        for d in details:
            if d.salary_component == "JHT Perusahaan 3,7%": row["jht_company"] += d.amount
            elif d.salary_component == "JKK 0,89%": row["jkk"] += d.amount
            elif d.salary_component == "JKM 0,3%": row["jkm"] += d.amount
            elif d.salary_component == "JP Perusahaan 2%": row["jp_company"] += d.amount
            elif d.salary_component == "JKN Perusahaan 4%": row["jkn_company"] += d.amount
            elif d.salary_component == "JHT Karyawan 2%": row["jht_employee"] += d.amount
            elif d.salary_component == "JP Karyawan 1%": row["jp_employee"] += d.amount
            elif d.salary_component == "JKN Karyawan 1%": row["jkn_employee"] += d.amount
            
        # Jika slip ini tidak memiliki satupun komponen BPJS, lewati saja
        if row["jht_company"] == 0 and row["jht_employee"] == 0 and row["jkn_company"] == 0 and row["jkn_employee"] == 0:
            continue
            
        # Reverse engineer nilai Gaji Dilaporkan
        if row["jht_company"] > 0:
            row["reported_salary"] = round(row["jht_company"] / 0.037)
        elif row["jkk"] > 0:
            row["reported_salary"] = round(row["jkk"] / 0.0089)
        elif row["jkn_company"] > 0:
            row["reported_salary"] = round(row["jkn_company"] / 0.04)
            
        row["total_company"] = row["jht_company"] + row["jkk"] + row["jkm"] + row["jp_company"] + row["jkn_company"]
        row["total_employee"] = row["jht_employee"] + row["jp_employee"] + row["jkn_employee"]
        row["total_all"] = row["total_company"] + row["total_employee"]
        
        data.append(row)
        
    return data
