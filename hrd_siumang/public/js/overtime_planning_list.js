frappe.listview_settings["Overtime Planning"] = {
	get_indicator: function (doc) {
		// Mapping dari status ke warna dan teks
		const status_map = {
			Draft: ["gray", "Draft"],
			"Pending L1 Approval": ["orange", "Pending L1"],
			"Pending HR Review": ["blue", "Pending HR Review"],
			"Pending HR Manager Approval": ["purple", "Pending HR Mgr"],
			"Approved by HR": ["green", "Approved by HR"],
			Submitted: ["green", "Submitted"],
			Rejected: ["red", "Rejected"],
			Cancelled: ["red", "Cancelled"],
		};
		const [color, status_text] = status_map[doc.status] || ["darkgrey", doc.status];
		return [__(status_text), color, "status,=," + doc.status];
	},
	// Menambahkan fungsi get_workflow_actions untuk menampilkan aksi dinamis
	get_workflow_actions: function (doc) {
		return frappe
			.call({
				method: "hrd_siumang.doc_events.overtime_planning_events.get_workflow_actions_for_overtime_planning",
				args: {
					doc: doc,
					workflow_name: "Overtime Planning Approval Workflow", // Pastikan nama workflow sesuai
				},
				async: false, // Menjadikan panggilan sinkron untuk kompatibilitas
			})
			.then((r) => {
				if (r.message) {
					return r.message;
				}
				return [];
			});
	},
};
