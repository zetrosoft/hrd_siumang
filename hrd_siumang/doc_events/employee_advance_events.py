# Adapted from employee_portal.doc_events.expense_claim_notification
import frappe
from frappe import _


def send_notification_on_state_change(doc, method=None):
	"""Sends bell notifications for Employee Advance workflow state changes."""
	doc_before_save = doc.get_doc_before_save()
	if not doc_before_save:
		return

	new_state = doc.workflow_state
	old_state = doc_before_save.workflow_state

	if new_state == old_state:
		return

	owner_name = frappe.get_value("User", doc.owner, "full_name") or doc.owner
	subject = ""
	content = ""
	recipients = []

	# 1. Employee -> Manager
	if new_state == "Pending Manager Approval":
		subject = f"Employee Advance {doc.name} from {owner_name} needs your approval"
		content = f"Please review and approve the Employee Advance {doc.name}."
		if doc.expense_approver:
			recipients = [doc.expense_approver]
		else:
			recipients = get_users_with_role("Manager")

	# 2. Manager -> Finance Reviewer
	elif new_state == "Pending Finance Review":
		subject = f"Employee Advance {doc.name} has been approved by Manager"
		content = f"Please review the Employee Advance {doc.name} for financial checking."
		recipients = get_users_with_role("Accounts User")

	# 3. Finance Reviewer -> Accounts Manager
	elif new_state == "Pending AM Approval":
		subject = f"Employee Advance {doc.name} is ready for your approval"
		content = f"Please review and approve the Employee Advance {doc.name}."
		recipients = get_users_with_role("Accounts Manager")

	# 4. Accounts Manager -> Director (Value >= 10jt)
	elif new_state == "Pending Director Approval":
		subject = f"Employee Advance {doc.name} from {owner_name} needs your approval"
		content = f"Employee Advance {doc.name} with amount {doc.get_formatted('advance_amount')} requires your approval."
		recipients = get_users_with_role("Director")

	# 5. Final Approval
	elif new_state == "Approved":
		subject = f"Your Employee Advance {doc.name} has been approved"
		content = f"Your Employee Advance {doc.name} has been fully approved."
		recipients = [doc.owner]

	# 6. Rejection
	elif new_state == "Rejected":
		rejected_by = frappe.get_value("User", frappe.session.user, "full_name") or frappe.session.user
		subject = f"Your Employee Advance {doc.name} has been rejected"
		content = f"Your Employee Advance {doc.name} was rejected by {rejected_by}."
		recipients = [doc.owner]

	if recipients:
		for user in set(recipients):
			create_bell_notification(doc, subject, content, user)


def create_bell_notification(doc, subject, content, user):
	"""Helper function to create a bell-only Notification Log entry."""
	if not user or not frappe.db.exists("User", user):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"type": "Alert",
				"channel": "System Notification",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"subject": subject,
				"for_user": user,
			}
		).insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(
			f"Failed to create notification for {user} on {doc.name}: {e}",
			"Employee Advance Notification Error",
		)


def get_users_with_role(role_name):
	"""Returns a list of enabled users with a given role."""
	return [
		p[0]
		for p in frappe.db.sql(
			"""SELECT T1.name
            FROM `tabUser` T1, `tabHas Role` T2
            WHERE T1.name = T2.parent
            AND T2.role = %s
            AND T1.enabled = 1""",
			role_name,
		)
	]
