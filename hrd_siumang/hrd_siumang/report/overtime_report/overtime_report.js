// Copyright (c) 2026, Bijak Techno and contributors
// For license information, please see license.txt

frappe.query_reports["Overtime Report"] = {
	filters: [
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "payroll_period",
			label: __("Payroll Period"),
			fieldtype: "Link",
			options: "Payroll Period",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: function () {
				const payroll_period = frappe.query_report.get_filter_value("payroll_period");
				return {
					query: "hrd_siumang.hrd_siumang.report.overtime_report.overtime_report.get_employees_with_overtime",
					filters: {
						payroll_period: payroll_period,
					},
				};
			},
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "total_hours" && data && data.calculation_tooltip) {
			value = `<span class="indicator-blue" title="${data.calculation_tooltip}" style="cursor: help; border-bottom: 1px dashed #2490ef;">${value}</span>`;
		}

		return value;
	},
};
