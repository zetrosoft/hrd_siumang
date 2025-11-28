import frappe


def create_custom_payslip_print_format():
	"""
	Creates or updates a custom Print Format for Salary Slip to match a specific design.
	Sets it as the default format for the Salary Slip Doctype.
	"""
	frappe.set_user("Administrator")

	pf_name = "Slip Gaji Kustom Siumang"
	doctype_name = "Salary Slip"

	# CSS content designed to match the provided JPG image
	css_content = """
        .payslip-container {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 9pt;
            color: #333;
            max-width: 800px;
            margin: auto;
            padding: 15px;
            background-color: #fff;
        }
        .header-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        .header-table td {
            vertical-align: top;
            padding: 0;
        }
        .header-logo-cell {
            width: 15%;
            text-align: left;
        }
        .header-logo img {
            max-width: 60px;
            height: auto;
        }
        .header-title-cell {
            width: 70%;
            text-align: center;
        }
        .header-title-cell p {
            font-size: 9pt;
            font-weight: bold;
            margin: 0;
            padding-top: 5px; /* Adjust as needed */
        }
        .header-title-cell h1 {
            font-size: 16pt;
            font-weight: bold;
            margin: 0;
            padding-bottom: 5px; /* Adjust as needed */
        }
        .employee-details-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .employee-details-table td {
            padding: 2px 5px;
            vertical-align: top;
            white-space: nowrap; /* Prevents wrapping for labels */
        }
        .employee-details-table td:nth-child(1),
        .employee-details-table td:nth-child(4) {
            width: 10%; /* Label width */
        }
        .employee-details-table td:nth-child(2),
        .employee-details-table td:nth-child(5) {
            width: 1%; /* Colon width */
        }
        .employee-details-table td:nth-child(3),
        .employee-details-table td:nth-child(6) {
            width: 39%; /* Value width */
        }

        .main-content-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .main-content-table th {
            text-align: left;
            padding: 5px 0;
            border-bottom: 1px solid #000;
            font-size: 10pt;
        }
        .main-content-table td {
            vertical-align: top;
            padding: 0;
            width: 50%;
        }
        .component-table {
            width: 100%;
        }
        .component-table td {
            padding: 2px 0;
            border: none;
            font-size: 9pt;
            line-height: 1.2; /* Adjust line height for better spacing */
        }
        .component-name {
            width: 65%; /* Adjusted width */
            text-align: left;
            padding-left: 5px;
        }
        .component-colon {
            width: 1%;
            text-align: center;
        }
        .component-currency {
            width: 5%; /* Adjusted width */
            text-align: left;
        }
        .component-amount {
            width: 29%; /* Adjusted width */
            text-align: right;
            padding-right: 5px;
        }
        .summary-row td {
            padding-top: 8px;
        }
        .summary-label {
            font-weight: bold;
        }
        .summary-amount {
            font-weight: bold;
            text-align: right;
            border-top: 1px solid #000;
            border-bottom: 2px solid #000; /* Thicker bottom border */
        }
        .bank-details-table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }
        .bank-details-table td {
            vertical-align: bottom;
            padding: 0;
        }
        .bank-info-cell {
            width: 50%;
            text-align: left;
            padding-left: 5px;
        }
        .take-home-pay-cell {
            width: 50%;
            text-align: right;
        }
        .take-home-pay-table {
            width: 100%;
            margin-top: 10px;
        }
        .take-home-pay-table td {
            padding: 2px 0;
            border: none;
            font-size: 9pt;
        }
        .take-home-pay-label {
            font-weight: bold;
            text-align: left;
            width: 65%;
            padding-left: 5px;
        }
        .take-home-pay-colon {
             width: 1%;
             text-align: center;
        }
        .take-home-pay-currency {
            width: 5%;
            text-align: left;
        }
        .take-home-pay-amount {
            font-weight: bold;
            text-align: right;
            font-size: 11pt;
            border-top: 1px solid #000;
            border-bottom: 3px double #000;
            padding-right: 5px;
        }
        .footer-content {
            margin-top: 30px;
            font-size: 8pt;
        }
        .print-date {
            text-align: right;
            margin-bottom: 10px;
            padding-right: 5px;
        }
        .disclaimer {
            border: 1px solid #000;
            padding: 10px;
            text-align: center;
            line-height: 1.3;
        }
    """

	# HTML Jinja Template content to match the provided JPG image
	html_content = """
<div class="payslip-container">
    <table class="header-table">
        <tr>
            <td class="header-logo-cell">
                {% set company_logo = frappe.db.get_value("Company", doc.company, "company_logo") %}
                {% if company_logo %}
                    <img class="header-logo" src="{{ company_logo }}" alt="Logo">
                {% endif %}
            </td>
            <td class="header-title-cell">
                <p>{{ frappe.db.get_value("Company", doc.company, "company_name") or "N/A" }}</p>
                <h1>SLIP GAJI {{ frappe.format(doc.end_date, "MMMM YYYY", doc=doc).upper() }}</h1>
            </td>
            <td></td> {# Empty cell for alignment #}
        </tr>
    </table>

    <table class="employee-details-table">
        <tr>
            <td>Name</td><td>:</td><td>{{ doc.employee_name }}</td>
            <td>Dept</td><td>:</td><td>{{ frappe.db.get_value("Employee", doc.employee, "department") or "N/A" }}</td>
        </tr>
        <tr>
            <td>Employee No.</td><td>:</td><td>{{ doc.employee }}</td>
            <td>Tax Ref No</td><td>:</td><td>{{ frappe.db.get_value("Employee", doc.employee, "npwp") or "N/A" }}</td>
        </tr>
        <tr>
            <td>Position</td><td>:</td><td>{{ frappe.db.get_value("Employee", doc.employee, "designation") or "N/A" }}</td>
            <td>Status</td><td>:</td><td>{{ frappe.db.get_value("Employee", doc.employee, "status_pajak") or "N/A" }}</td>
        </tr>
    </table>

    <table class="main-content-table">
        <thead>
            <tr>
                <th style="width: 50%;">I. Pendapatan</th>
                <th style="width: 50%;">II. Potongan</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>
                    <table class="component-table">
                        {% for item in doc.earnings %}
                        <tr>
                            <td class="component-name">{{ item.salary_component }}</td>
                            <td class="component-colon">:</td>
                            <td class="component-currency">Rp.</td>
                            <td class="component-amount">{{ frappe.format_money(item.amount, doc.currency, precision=0) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </td>
                <td>
                    <table class="component-table">
                        {% for item in doc.deductions %}
                        <tr>
                            <td class="component-name">{{ item.salary_component }}</td>
                            <td class="component-colon">:</td>
                            <td class="component-currency">Rp.</td>
                            <td class="component-amount">{{ frappe.format_money(item.amount, doc.currency, precision=0) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </td>
            </tr>
            <tr class="summary-row">
                <td>
                    <table class="component-table">
                        <tr>
                            <td class="summary-label component-name">Total Pendapatan</td>
                            <td class="component-colon">:</td>
                            <td class="component-currency">Rp.</td>
                            <td class="summary-amount component-amount">{{ frappe.format_money(doc.gross_pay, doc.currency, precision=0) }}</td>
                        </tr>
                    </table>
                </td>
                <td>
                    <table class="component-table">
                        <tr>
                            <td class="summary-label component-name">Total Potongan</td>
                            <td class="component-colon">:</td>
                            <td class="component-currency">Rp.</td>
                            <td class="summary-amount component-amount">{{ frappe.format_money(doc.total_deduction, doc.currency, precision=0) }}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>

    <table class="bank-details-table">
        <tr>
            <td class="bank-info-cell">
                No. Rekening {{ frappe.db.get_value("Employee", doc.employee, "bank_name") or "N/A" }} : {{ frappe.db.get_value("Employee", doc.employee, "bank_ac_no") or "N/A" }}<br>
                An. {{ doc.employee_name }}
            </td>
            <td class="take-home-pay-cell">
                 <table class="take-home-pay-table">
                    <tr>
                        <td class="take-home-pay-label">Take Home Pay</td>
                        <td class="take-home-pay-colon">:</td>
                        <td class="take-home-pay-currency">Rp.</td>
                        <td class="take-home-pay-amount">{{ frappe.format_money(doc.net_pay, doc.currency, precision=0) }}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <div class="footer-content">
        <p class="print-date">Dicetak : {{ frappe.format(frappe.utils.now(), "dd-MMM-yyyy HH:mm") }}</p>
        <div class="disclaimer">
            Slip gaji ini dicetak secara sistem dan sah tanpa tanda tangan. Informasi yang tercantum bersifat rahasia dan hanya diperuntukkan bagi karyawan yang bersangkutan
        </div>
    </div>
</div>
"""

	# Check if Print Format already exists, then create or update it
	if frappe.db.exists("Print Format", pf_name):
		print(f"✅ Print Format '{pf_name}' sudah ada. Memperbarui...")
		pf = frappe.get_doc("Print Format", pf_name)
	else:
		print(f"✅ Membuat Print Format baru '{pf_name}'...")
		pf = frappe.new_doc("Print Format")
		pf.name = pf_name

	pf.doc_type = doctype_name
	pf.print_format_type = "Jinja"  # Ensure it is Jinja for templates
	pf.html = html_content
	pf.css = css_content
	pf.standard = "No"

	try:
		pf.save(ignore_permissions=True)
		frappe.db.commit()
		print(f"✅ Print Format '{pf_name}' berhasil dibuat/diperbarui.")

		# Set as default via Print Settings (if applicable, Frappe version dependent)
		# Note: This might override other doctypes' default print formats if not specific enough.
		# A more robust solution might involve setting it via the UI or a custom property setter.
		frappe.db.set_value("Print Settings", "Print Settings", "default_print_format", pf_name, True)
		frappe.db.commit()
		print(f"✅ Print Format '{pf_name}' disetel sebagai default untuk '{doctype_name}'.")

	except Exception as e:
		frappe.db.rollback()
		print(f"❌ Gagal membuat/memperbarui Print Format '{pf_name}': {e}")
		frappe.log_error(frappe.get_traceback(), "Gagal Membuat Print Format Kustom")
