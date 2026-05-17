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
    if not filters.get("month") or not filters.get("year"):
        return []

    # Pastikan filter bulan dan tahun adalah integer
    month = int(filters.get("month"))
    year = int(filters.get("year"))
    
    conditions = ["ss.docstatus = 1", "MONTH(ss.start_date) = %(month)s", "YEAR(ss.start_date) = %(year)s"]
    query_args = {"month": month, "year": year}

    if filters.get("employee"):
        conditions.append("ss.employee = %(employee)s")
        query_args["employee"] = filters.get("employee")

    # Ambil data slip dan rincian komponen BPJS secara spesifik per tabel
    raw_data = frappe.db.sql(f"""
        SELECT 
            ss.employee,
            ss.employee_name,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'Gaji Pokok' THEN sd.amount ELSE 0 END) as base_gaji,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'Tj. Jabatan' THEN sd.amount ELSE 0 END) as base_jabatan,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'Tj. Komunikasi' THEN sd.amount ELSE 0 END) as base_komunikasi,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'JHT Perusahaan 3,7%%' THEN sd.amount ELSE 0 END) as jht_company,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'JKK 0,89%%' THEN sd.amount ELSE 0 END) as jkk,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'JKM 0,3%%' THEN sd.amount ELSE 0 END) as jkm,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'JP Perusahaan 2%%' THEN sd.amount ELSE 0 END) as jp_company,
            SUM(CASE WHEN sd.parentfield = 'earnings' AND sd.salary_component = 'JKN Perusahaan 4%%' THEN sd.amount ELSE 0 END) as jkn_company,
            SUM(CASE WHEN sd.parentfield = 'deductions' AND sd.salary_component = 'JHT Karyawan 2%%' THEN sd.amount ELSE 0 END) as jht_employee,
            SUM(CASE WHEN sd.parentfield = 'deductions' AND sd.salary_component = 'JP Karyawan 1%%' THEN sd.amount ELSE 0 END) as jp_employee,
            SUM(CASE WHEN sd.parentfield = 'deductions' AND sd.salary_component = 'JKN Karyawan 1%%' THEN sd.amount ELSE 0 END) as jkn_employee
        FROM 
            `tabSalary Slip` ss
        JOIN 
            `tabSalary Detail` sd ON ss.name = sd.parent
        WHERE 
            {" AND ".join(conditions)}
        GROUP BY 
            ss.employee, ss.employee_name
    """, query_args, as_dict=1)

    # Ambil BPJS Setting untuk mapping pengecualian gaji
    bpjs_setting = frappe.get_doc("BPJS Setting") if frappe.db.exists("BPJS Setting", "BPJS Setting") else None
    pengecualian_map = {}
    if bpjs_setting and hasattr(bpjs_setting, "pengecualian_gaji"):
        for exc in bpjs_setting.pengecualian_gaji:
            if exc.reported_salary:
                pengecualian_map[exc.employee] = exc.reported_salary

    data = []
    for row in raw_data:
        # Hitung internal base dari slip (Gaji Pokok + Tunjangan Tetap)
        internal_base = row["base_gaji"] + row["base_jabatan"] + row["base_komunikasi"]
        
        # Tentukan Gaji Dilaporkan
        row["reported_salary"] = pengecualian_map.get(row["employee"], internal_base)
        
        row["total_company"] = row["jht_company"] + row["jkk"] + row["jkm"] + row["jp_company"] + row["jkn_company"]
        row["total_employee"] = row["jht_employee"] + row["jp_employee"] + row["jkn_employee"]
        row["total_all"] = row["total_company"] + row["total_employee"]
        
        if row["total_all"] > 0:
            data.append(row)
            
    return data
