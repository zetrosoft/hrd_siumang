import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


@frappe.whitelist()
def is_user_department_manager(department: str) -> bool:
	# ... (code for this function remains the same)
	current_user = frappe.session.user
	if not current_user or not department:
		return False
	if "System Manager" in frappe.get_roles(current_user):
		return True
	is_manager_of_department = frappe.db.exists(
		"Employee", {"user_id": current_user, "department": department}
	)
	if not is_manager_of_department:
		return False
	if "Manager" not in frappe.get_roles(current_user):
		return False
	return True


def on_update(doc: Document, method: str):
	frappe.msgprint("DEBUG: on_update hook for Job Requisition triggered.")
	doc_before_save = doc.get_doc_before_save()
	if not doc_before_save:
		frappe.msgprint("DEBUG: doc_before_save is None (likely new doc).")
		return

	if doc_before_save.workflow_state == doc.workflow_state and not frappe.flags.in_test:
		frappe.msgprint(
			f"DEBUG: Workflow state is same ({doc.workflow_state}), not logging history or sending notifications."
		)
		return

	frappe.msgprint(
		f"DEBUG: Workflow state changed from {doc_before_save.workflow_state} to {doc.workflow_state}."
	)

	# Add to approval history first
	add_approval_history_log(doc)
	frappe.msgprint(
		f"DEBUG: add_approval_history_log called. Current history count: {len(doc.get('approval_history'))}"
	)

	# --- NOTIFICATIONS ---
	workflow_state = doc.workflow_state
	if frappe.flags.in_notification_hook:
		frappe.msgprint("DEBUG: Already in notification hook, returning.")
		return

	frappe.flags.in_notification_hook = True
	try:
		if workflow_state == "Pending Manager Approval":
			notify_manager_on_submission(doc)
		elif workflow_state == "Pending HR Manager Approval":
			notify_hr_manager_after_manager_approval(doc)
		elif workflow_state == "Pending Director Approval":
			notify_director_on_hr_processing(doc)
		elif workflow_state == "Submitted":
			notify_on_final_approval(doc)
		elif workflow_state == "Rejected":
			notify_on_rejection(doc)
			if doc.docstatus != 2:
				doc.cancel()
	finally:
		frappe.flags.in_notification_hook = False


def add_approval_history_log(doc: Document):
	"""Appends a new row to the 'approval_history' child table."""
	acting_user = frappe.session.user
	approver = doc.owner if not doc.get("approval_history") else acting_user

	frappe.msgprint(
		f"DEBUG: add_approval_history_log: Appending for state {doc.workflow_state} by {approver}."
	)

	doc.append(
		"approval_history",
		{
			"state": doc.workflow_state,
			"owner": doc.owner,
			"approval_by": approver,
			"approval_date": now_datetime(),
			"notification_status": "Sent",  # Placeholder, as we send notifications right after.
		},
	)
	frappe.msgprint(f"DEBUG: Row appended. Now {len(doc.get('approval_history'))} rows.")


# ... (all other functions remain the same)


def get_users_with_role_and_department(role: str, department: str) -> list[str]:
	if not department:
		return []
	employee_user_ids = frappe.get_all(
		"Employee", filters={"department": department, "status": "Active"}, fields=["user_id"]
	)
	user_ids = [e.user_id for e in employee_user_ids if e.user_id]
	if not user_ids:
		return []
	users_with_role = frappe.get_all(
		"Has Role",
		filters={"role": role, "parent": ["in", user_ids], "parenttype": "User"},
		fields=["parent"],
	)
	return [u.parent for u in users_with_role]


def send_notification(doc: Document, recipient_list: list[str], subject: str):
	if not recipient_list:
		return
	final_recipients = list(set(recipient_list))
	for user in final_recipients:
		notification_doc = frappe.new_doc("Notification Log")
		notification_doc.for_user = user
		notification_doc.document_type = doc.doctype
		notification_doc.document_name = doc.name
		notification_doc.subject = subject
		notification_doc.insert(ignore_permissions=True)


def notify_manager_on_submission(doc: Document):
	subject = f"Job Requisition {doc.name} requires your approval"
	managers = get_users_with_role_and_department("Manager", doc.department)
	send_notification(doc, managers, subject)


def notify_hr_manager_after_manager_approval(doc: Document):
	subject = f"Job Requisition {doc.name} approved by Manager, requires HR processing"
	hr_managers = frappe.get_all(
		"Has Role", filters={"role": "HR Manager", "parenttype": "User"}, fields=["parent"]
	)
	recipients = [u.parent for u in hr_managers]
	send_notification(doc, recipients, subject)


def notify_director_on_hr_processing(doc: Document):
	subject = f"Job Requisition {doc.name} for new addition requires Director's approval"
	directors = frappe.get_all(
		"Has Role", filters={"role": "Director", "parenttype": "User"}, fields=["parent"]
	)
	recipients = [u.parent for u in directors]
	send_notification(doc, recipients, subject)


def notify_on_final_approval(doc: Document):
	subject = f"Job Requisition {doc.name} has been fully approved and submitted"
	recipients = [doc.owner]
	managers = get_users_with_role_and_department("Manager", doc.department)
	recipients.extend(managers)
	hr_managers = frappe.get_all(
		"Has Role", filters={"role": "HR Manager", "parenttype": "User"}, fields=["parent"]
	)
	recipients.extend([u.parent for u in hr_managers])
	send_notification(doc, recipients, subject)


def notify_on_rejection(doc: Document):
	subject = f"Job Requisition {doc.name} has been rejected"
	recipients = [doc.owner]
	managers = get_users_with_role_and_department("Manager", doc.department)
	recipients.extend(managers)
	send_notification(doc, recipients, subject)
