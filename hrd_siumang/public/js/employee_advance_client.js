frappe.ui.form.on("Employee Advance", {
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.db.get_value("Employee", frm.doc.employee, "department").then((r) => {
				let department = r.message.department;
				if (department) {
					frappe.call({
						method: "hrd_siumang.utils.approvers.get_department_approver",
						args: { department_name: department },
						callback: function (res) {
							if (res.message) {
								frm.set_value("expense_approver", res.message);
							} else {
								frm.set_value("expense_approver", null);
								frappe.msgprint(
									__("No approver found for department {0}", [department])
								);
							}
						},
					});
				} else {
					frm.set_value("expense_approver", null);
				}
			});
		} else {
			frm.set_value("expense_approver", null);
		}
	},
});
