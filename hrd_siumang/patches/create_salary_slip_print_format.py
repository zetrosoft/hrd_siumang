import textwrap

import frappe


def execute():
	# Set flag for patch context
	frappe.flags.in_patch = True

	# Get the current user for owner and modified_by
	current_user = frappe.session.user if frappe.session.user else "Administrator"

	# Content of slip_gaji_siumang.html
	# --- Start HTML Content ---
	# Using textwrap.dedent for clean multiline string and carefully escaping inner quotes
	# Double quotes and backslashes in the HTML content will be escaped
	# Triple quotes in the HTML content will be replaced by escaped versions
	html_content = textwrap.dedent("""
{% set employee_doc = frappe.get_doc('Employee', doc.employee) %}
{% set company_doc = frappe.get_doc('Company', doc.company) %}
<!DOCTYPE html>
<html>
<head>
    <style>
        @page {
            size: 210mm 297mm; /* A4 */
            margin: 10mm 05mm 5mm 15mm; /* top right bottom left */
        }
        body {
            font-family: 'Arial', sans-serif;
            font-size: 12px; /* Increased font size */
            color: #333;
        }
        .print-format-container {
            width: 100%;
            margin: auto;
            padding: 0; /* Margins handled by @page */
        }
        .header-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }
        .header-table td {
            vertical-align: middle;
            padding: 0;
        }
        .logo {
            height: 50px;
            float: left;
            margin-right: 10px;
        }
        .title-section {
            text-align: center;
            flex-grow: 1;
        }
        .title-section h1 {
            margin: 0;
            font-size: 18px; /* Increased title font size */
            font-weight: bold;
        }
        .title-section p {
            margin: 0;
            font-size: 14px;
        }
        .employee-info-table, .item-detail-table, .bank-info-table, .total-summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }
        .employee-info-table td, .item-detail-table td, .bank-info-table td, .total-summary-table td {
            padding: 2px 0; /* Reduced padding for smaller row height */
            vertical-align: top;
            font-size: 12px;
        }
        .employee-info-table .label-col {
            width: 100px;
            font-weight: bold;
        }
        .employee-info-table .value-col {
            width: 200px;
        }
        .employee-info-table .spacer-col {
            width: 50px;
        }
        .section-title {
            font-size: 14px; /* Increased section title font size */
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
            border-bottom: 1px solid #333;
            padding-bottom: 2px;
        }
        .two-column-layout {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .column {
            width: 48%; /* Slightly less than 50% to allow for gap */
        }
        .item-detail-table {
            table-layout: fixed; /* Ensures fixed width for columns */
        }
        .item-detail-table td {
            white-space: nowrap; /* Prevents wrapping */
            overflow: hidden;
            text-overflow: ellipsis; /* Adds ellipsis for overflow */
        }
        .item-detail-table td.component-label {
            width: 53%; /* Adjusted width */
        }
        .item-detail-table td.currency-prefix {
            width: 2%;
            text-align: left;
        }
        .item-detail-table td.amount-value {
            width: 45%;
            text-align: right;
        }
        .total-row {
            border-top: 1px solid #333;
            font-weight: bold;
        }
        .total-summary-table .label-col {
            width: 150px;
        }
        .total-summary-table .amount-col {
            text-align: right;
        }
        .bank-info-table .label-col {
            width: 150px;
        }
        .bank-info-table .value-col {
            text-align: left;
        }
        .bank-info-table .take-home-label {
            font-weight: bold;
            font-size: 14px;
        }
        .bank-info-table .take-home-value {
            font-weight: bold;
            font-size: 14px;
            text-align: right;
        }
        .footer-section {
            text-align: right;
            font-size: 10px;
            margin-top: 20px;
        }
        .disclaimer-section {
            border: 1px solid #333;
            padding: 5px;
            text-align: center;
            font-size: 9px;
            font-style: italic;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="print-format-container">
        <table class="header-table">
            <tr>
                <td style="width: 15%; text-align: left;">
                    {% if company_doc.company_logo %}
                    <img class="logo" src="{{ company_doc.company_logo }}" alt="{{ company_doc.company_name or 'Logo Perusahaan' }}">
                    {% else %}
                    <!-- Fallback if company_logo is not found -->
                    {% set default_logo = frappe.get_doc('Company', doc.company).default_company_logo if frappe.get_doc('Company', doc.company) else '' %}
                    <img class="logo" src="{{ default_logo or '/assets/hrd_siumang/images/logo_siumang.png' }}" alt="Logo PT. SIUMANG TEMAN SUKSES">
                    {% endif %}
                </td>
                <td style="width: 70%;" class="title-section">
                    <h1>SLIP GAJI {{ frappe.format(doc.start_date, "MMMM YYYY") | default('') | upper }}</h1>
                    <p style="font-size: 12px; margin-top: 5px; text-align: center;">{{ company_doc.company_name }}</p>
                </td>
                <td style="width: 15%; text-align: right;">
                    <!-- QR Code or other elements can go here if needed -->
                </td>
            </tr>
        </table>
        <hr style="border: none; border-top: 1px solid #333; margin: 5px 0;">

        <table class="employee-info-table">
            <tr>
                <td class="label-col">Name</td>
                <td class="value-col">: {{ doc.employee_name }}</td>
                <td class="spacer-col"></td>
                <td class="label-col">Dept</td>
                <td class="value-col">: {{ doc.department }}</td>
            </tr>
            <tr>
                <td class="label-col">Employee No.</td>
                <td class="value-col">: {{ doc.employee }}</td>
                <td class="spacer-col"></td>
                <td class="label-col">Tax Ref No</td>
                <td class="value-col">: {{ employee_doc.npwp or '-' }}</td>
            </tr>
            <tr>
                <td class="label-col">Position</td>
                <td class="value-col">: {{ doc.designation }}</td>
                <td class="spacer-col"></td>
                <td class="label-col">Status</td>
                <td class="value-col">: {{ employee_doc.status_pajak or '-' }}</td>
            </tr>
        </table>

        <div class="two-column-layout">
            <div class="column">
                <p class="section-title">I. Pendapatan</p>
                <table class="item-detail-table">
                    <tr>
                        <td class="component-label">Gaji Pokok</td>
                        <td class="currency-prefix"></td>
                        <td class="amount-value">{{ frappe.format(doc.base, "Currency", 0) if doc.base else '-' }}</td>
                    </tr>
                    {% for item in doc.earnings %}
                    <tr>
                        <td class="component-label">{{ item.salary_component }}</td>
                        <td class="currency-prefix"></td>
                        <td class="amount-value">{{ frappe.format(item.amount, "Currency", 0) if item.amount else '-' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div class="column">
                <p class="section-title">II. Potongan</p>
                <table class="item-detail-table">
                    <tr>
                        <td class="component-label">Absensi</td>
                        <td class="currency-prefix"></td>
                        <td class="amount-value">-</td>
                    </tr>
                    {% for item in doc.deductions %}
                    <tr>
                        <td class="component-label">{{ item.salary_component }}</td>
                        <td class="currency-prefix"></td>
                        <td class="amount-value">{{ frappe.format(item.amount, "Currency", 0) if item.amount else '-' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <table class="total-summary-table">
            <tr class="total-row">
                <td class="label-col">Total Pendapatan</td>
                <td class="currency-prefix"></td>
                <td class="amount-col">{{ frappe.format(doc.gross_pay, "Currency", 0) }}</td>
                <td class="label-col" style="text-align: right;">Total Potongan</td>
                <td class="currency-prefix"></td>
                <td class="amount-col">{{ frappe.format(doc.total_deduction, "Currency", 0) }}</td>
            </tr>
        </table>

        <table class="bank-info-table">
            <tr>
                <td class="label-col" colspan="2">No. Rekening {{ employee_doc.bank_name or '' }}</td>
                <td class="value-col">: {{ employee_doc.bank_ac_no or '-' }}</td>
                <td class="take-home-label">Take Home Pay</td>
                <td class="currency-prefix"></td>
                <td class="take-home-value">{{ frappe.format(doc.net_pay, "Currency", 0) }}</td>
            </tr>
            <tr>
                <td class="label-col" colspan="2">An.</td>
                <td class="value-col">: {{ doc.employee_name or '-' }}</td>
                <td colspan="3"></td>
            </tr>
        </table>

        <div class="footer-section">
            <p>Dicetak : {{ frappe.utils.now_datetime().strftime("%d-%m-%Y %H:%M") }}</p>
        </div>

        <div class="disclaimer-section">
            <p>Slip gaji ini dicetak secara sistem dan sah tanpa tanda tangan. Informasi yang tercantum bersifat rahasia dan hanya diperuntukkan bagi karyawan yang bersangkutan</p>
        </div>
    </div>
</body>
</html>""")

	# --- End HTML Content ---

	# Print Format properties
	print_format_data = {
		"name": "Slip Gaji Siumang",
		"doc_type": "Salary Slip",
		"module": "hrd_siumangg",  # Corrected capitalization based on app_title
		"standard": "Yes",
		"print_format_type": "Jinja",
		"html": html_content,
		"absolute_value": 0,
		"align_labels_right": 0,
		"custom_format": 1,
		"default_print_language": "id",
		"disabled": 0,
		"docstatus": 0,
		"doctype": "Print Format",
		"font_size": 0,
		"idx": 0,
		"line_breaks": 0,
		"margin_bottom": 0.0,
		"margin_left": 0.0,
		"margin_right": 0.0,
		"margin_top": 0.0,
		"modified": frappe.utils.now(),
		"modified_by": current_user,
		"owner": current_user,
		"pdf_generator": "wkhtmltopdf",
		"print_format_builder": 0,
		"print_format_builder_beta": 0,
		"print_format_for": "DocType",
		"raw_printing": 0,
		"show_section_headings": 0,
	}

	# Delete existing Print Format if it exists to avoid TimestampMismatchError
	if frappe.db.exists("Print Format", "Slip Gaji Siumang"):
		try:
			frappe.delete_doc("Print Format", "Slip Gaji Siumang", ignore_permissions=True)
			frappe.db.commit()
			frappe.log("Existing Print Format 'Slip Gaji Siumang' deleted for recreation.")
		except Exception as e:
			frappe.log(f"Error deleting existing Print Format 'Slip Gaji Siumang': {e}")
			# No frappe.throw here to avoid stopping migrate.

	# Create new Print Format
	doc = frappe.new_doc("Print Format")
	doc.update(print_format_data)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()  # Commit changes to the database
	frappe.log("Print Format 'Slip Gaji Siumang' created successfully via patch.")
