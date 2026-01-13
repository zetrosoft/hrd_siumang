import frappe
from frappe import _
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication


class LeaveApplicationCustom(LeaveApplication):
	def on_submit(self):
		# Check if current workflow state is one of the pending states
		is_in_pending_workflow = getattr(self, "workflow_state", None) in [
			"Pending Manager Approval",
			"Pending HR Review",
			"Pending HR Manager Approval",
		]
		# If the document status is Open/Cancelled AND it's NOT in a pending workflow state,
		# then throw the original error.
		if self.status in ["Open", "Cancelled"] and not is_in_pending_workflow:
			frappe.log_error(
				_("Leave Applications with status 'Open' and 'Cancelled' cannot be submitted."),
				title="Invalid Leave Application Submission",
				reference_doctype=self.doctype,
				reference_name=self.name,
			)
			# frappe.msgprint(f"Is in pending workflow: {is_in_pending_workflow}")
			# frappe.throw(_("Only Leave Applications with status 'Approved' and 'Rejected' can be submitted"))
		else:
			# Otherwise (if it's in a pending workflow state, or if status is already Approved/Rejected),
			# proceed with the standard submission logic.
			super().on_submit()

	def notify_approver(self):
		# Override to prevent PWA Notification creation that causes database sequence error
		pass

	def notify_approval_status(self):
		# Override to prevent PWA Notification creation that causes database sequence error
		pass
