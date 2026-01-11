// This script combines standard HRMS Job Requisition client-side functionality
// with custom logic to manage workflow action button visibility.

frappe.ui.form.on("Job Requisition", {
	refresh: function (frm) {
		console.log("HRD Siumang DEBUG: job_requisition_workflow.js refresh event triggered.");
		console.log("HRD Siumang DEBUG: Current User:", frappe.session.user);
		console.log("HRD Siumang DEBUG: Document Department:", frm.doc.department);
		console.log("HRD Siumang DEBUG: Document Workflow State:", frm.doc.workflow_state);
		console.log("HRD Siumang DEBUG: Is New Document:", frm.is_new());

		// --- Start: Standard HRMS Job Requisition Client Script Logic ---
		// This section is copied from hrms/hrms/hr/doctype/job_requisition/job_requisition.js

		if (!frm.doc.__islocal && !["Filled", "On Hold", "Cancelled"].includes(frm.doc.status)) {
			frappe.db
				.get_list("Employee Referral", {
					filters: { for_designation: frm.doc.designation, status: "Pending" },
				})
				.then((data) => {
					if (data && data.length) {
						const link =
							data.length > 1
								? `<a id="referral_links" style="text-decoration: underline;">${__(
										"Employee Referrals"
								  )}</a>`
								: `<a id="referral_links" style="text-decoration: underline;">${__(
										"Employee Referral"
								  )}</a>`;

						const headline = __("{} {} open for this position.", [data.length, link]);
						frm.dashboard.clear_headline();
						frm.dashboard.set_headline(headline, "yellow");

						$("#referral_links").on("click", (e) => {
							e.preventDefault();
							frappe.set_route("List", "Employee Referral", {
								for_designation: frm.doc.designation,
								status: "Pending",
							});
						});
					}
				});
		}

		if (frm.doc.status === "Open & Approved") {
			frm.add_custom_button(
				__("Create Job Opening"),
				() => {
					frappe.model.open_mapped_doc({
						method: "hrms.hr.doctype.job_requisition.job_requisition.make_job_opening",
						frm: frm,
					});
				},
				__("Actions")
			);

			frm.add_custom_button(
				__("Associate Job Opening"),
				() => {
					frappe.prompt(
						{
							label: __("Job Opening"),
							fieldname: "job_opening",
							fieldtype: "Link",
							options: "Job Opening",
							reqd: 1,
							get_query: () => {
								const filters = {
									company: frm.doc.company,
									status: "Open",
									designation: frm.doc.designation,
								};

								if (frm.doc.department) filters.department = frm.doc.department;

								return { filters: filters };
							},
						},
						(values) => {
							frm.call("associate_job_opening", { job_opening: values.job_opening });
						},
						__("Associate Job Opening"),
						__("Submit")
					);
				},
				__("Actions")
			);

			frm.page.set_inner_btn_group_as_primary(__("Actions"));
		}
		// --- End: Standard HRMS Job Requisition Client Script Logic ---

		// --- Start: Custom Workflow Button Visibility Logic ---
		// This logic controls the visibility of workflow action buttons based on user permissions.

		if (frm.doc.workflow_state === "Pending Manager Approval" && !frm.is_new()) {
			// If the current user is Administrator, assume full permission.
			if (frappe.session.user === "Administrator") {
				console.log(
					"HRD Siumang DEBUG: User is Administrator, assuming full workflow permission."
				);
				frm.refresh_workflow_actions();
			} else {
				// Call the whitelisted server method to check if the current user
				// is the designated manager for this document's department.
				frappe.call({
					method: "hrd_siumang.hrd_siumang.doc_events.job_requisition_events.is_user_department_manager",
					args: {
						department: frm.doc.department,
					},
					callback: function (r) {
						if (r.message) {
							console.log(
								"HRD Siumang DEBUG: User is authorized manager, showing workflow actions."
							);
							frm.refresh_workflow_actions();
						} else {
							console.log(
								"HRD Siumang DEBUG: User is NOT authorized manager, hiding workflow actions."
							);
							frm.page.clear_actions_menu();
							frm.page.actions_menu.empty(); // Ensure workflow actions are also cleared
						}
					},
				});
			}
		} else {
			// For other workflow states, or if it's a new doc, Frappe's default permission handling for workflow actions applies.
			// Ensure no custom hiding interferes.
			frm.refresh_workflow_actions();
		}
		// --- End: Custom Workflow Button Visibility Logic ---

		// --- Start: AGGRESSIVE: Ensure Approval History Tab and Field are Visible ---
		// This attempts to forcefully show the tab and its field, in case other scripts are hiding it.
		// This is moved to the end to run after other scripts might have hidden it.
		frm.toggle_tab_break("approval_history_tab", true); // Ensure the Tab Break is visible
		frm.toggle_display("approval_history", true); // Ensure the Table field within the tab is visible
		console.log("HRD Siumang DEBUG: Forcing 'Approval History' tab and field to be visible.");
		// --- End: AGGRESSIVE Logic ---
	},
});
