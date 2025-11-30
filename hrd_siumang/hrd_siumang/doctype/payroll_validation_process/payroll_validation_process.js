// payroll_validation_process.js
frappe.ui.form.on("Payroll Validation Process", {
	refresh: function (frm) {
		frm.clear_custom_buttons();

		// Add a custom button for "Run Validation"
		frm.add_custom_button(__("Run Validation"), function () {
			// Call the whitelisted method on the document's class
			frm.call("run_validation").then((r) => {
				if (r.message && r.message.status === "enqueued") {
					frappe.show_alert({
						message: __("Validation process has been started in the background."),
						indicator: "info",
					});
				}
			});
		}).addClass("btn-primary");

		// Add a custom button for "Process Absences"
		frm.add_custom_button(__("Process Absences"), function () {
			frappe.confirm(
				__(
					"This will create leave applications for absent employees with leave balance. This action cannot be undone. Are you sure you want to continue?"
				),
				function () {
					// Call the whitelisted method on the document's class
					frm.call("process_absences").then((r) => {
						if (r.message && r.message.status === "enqueued") {
							frappe.show_alert({
								message: __(
									"Absence processing has been started in the background."
								),
								indicator: "info",
							});
						}
					});
				}
			);
		});
	},
});
