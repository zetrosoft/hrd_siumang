import frappe
from frappe import _


def check_l1_approver_permission(doc):
	"""
	Memeriksa apakah pengguna yang login saat ini adalah L1 Approver yang ditunjuk di dokumen.
	"""
	if frappe.session.user == doc.overtime_approver:
		return True
	return False


@frappe.whitelist()
def get_workflow_actions_for_overtime_planning(doc, workflow_name=None):
	"""
	Override default get_workflow_actions untuk menambahkan kondisi dinamis
	berdasarkan 'overtime_approver'.
	"""
	actions = []

	workflow = frappe.get_doc("Workflow", workflow_name)
	current_state_data = [d for d in workflow.states if d.state == doc.status]

	if not current_state_data:
		return actions

	current_state_allow_edit = current_state_data[0].allow_edit

	# Check if current user has edit permission for current state
	if current_state_allow_edit:
		allowed_roles = [role.strip() for role in current_state_allow_edit.split(",")]
		if not frappe.user.has_any_role(allowed_roles):
			return actions  # User cannot edit, so no actions

	for transition in workflow.transitions:
		if transition.state == doc.status:
			allowed_roles_for_transition = [role.strip() for role in transition.allowed.split(",")]

			# Khusus untuk transisi L1 Approve/Reject
			if transition.state == "Pending L1 Approval" and (
				transition.action == "Approve" or transition.action == "Reject"
			):
				if check_l1_approver_permission(doc):
					actions.append(transition.action)
			elif frappe.user.has_any_role(allowed_roles_for_transition):
				actions.append(transition.action)

	return actions


# ---- Notification Logics ----


def on_update_or_submit(doc, method):
	"""
	Dijalankan setiap kali Overtime Planning disimpan atau disubmit.
	Membuat notifikasi lonceng berdasarkan perubahan status workflow.
	"""
	# Notifikasi saat diajukan ke approver (dari Draft ke Pending L1 Approval)
	if doc.status == "Pending L1 Approval" and doc.get_doc_before_save().status != "Pending L1 Approval":
		create_notification_log(
			doc,
			_("Permintaan Persetujuan Lembur: {0}").format(doc.name),
			_("Dokumen Lembur {0} memerlukan persetujuan Anda. Dari {1}").format(doc.name, doc.owner),
			doc.overtime_approver,
		)

	# Notifikasi saat ditolak
	elif doc.status == "Rejected" and doc.get_doc_before_save().status in [
		"Pending L1 Approval",
		"Pending HR Manager Approval",
		"Approved by HR",
	]:
		create_notification_log(
			doc,
			_("Rencana Lembur Ditolak: {0}").format(doc.name),
			_("Dokumen Lembur {0} Anda telah ditolak oleh {1}.").format(doc.name, frappe.session.user),
			doc.owner,
		)

	# Notifikasi saat disetujui oleh L1 Approver (dari Pending L1 Approval ke Pending HR Review)
	elif doc.status == "Pending HR Review" and doc.get_doc_before_save().status == "Pending L1 Approval":
		hr_users = get_users_with_role("HR User")
		for user in hr_users:
			create_notification_log(
				doc,
				_("Rencana Lembur Siap Review HR: {0}").format(doc.name),
				_("Dokumen Lembur {0} telah disetujui L1 dan siap untuk di-review HR.").format(doc.name),
				user,
			)

	# Notifikasi saat diajukan ke HR Manager (dari Pending HR Review ke Pending HR Manager Approval)
	elif (
		doc.status == "Pending HR Manager Approval"
		and doc.get_doc_before_save().status == "Pending HR Review"
	):
		hr_managers = get_users_with_role("HR Manager")
		for user in hr_managers:
			create_notification_log(
				doc,
				_("Permintaan Persetujuan HR Manager: {0}").format(doc.name),
				_("Dokumen Lembur {0} menunggu persetujuan Anda.").format(doc.name),
				user,
			)

	# Notifikasi saat disetujui oleh HR Manager (dari Pending HR Manager Approval ke Approved by HR)
	elif doc.status == "Approved by HR" and doc.get_doc_before_save().status == "Pending HR Manager Approval":
		recipients = [doc.owner]
		if doc.overtime_approver:
			recipients.append(doc.overtime_approver)

		for user in set(recipients):  # Kirim ke owner & L1 approver
			create_notification_log(
				doc,
				_("Rencana Lembur Disetujui HR: {0}").format(doc.name),
				_("Dokumen Lembur {0} telah disetujui oleh HR Manager dan siap untuk Submit Final.").format(
					doc.name
				),
				user,
			)


def create_notification_log(doc, subject, message, for_user):
	"""Membuat notifikasi lonceng (Notification Log)."""
	if not for_user or not frappe.db.exists("User", for_user):
		return

	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"document_type": doc.doctype,
			"document_name": doc.name,
			"for_user": for_user,
			"attached_to_doctype": doc.doctype,  # Untuk link langsung
			"attached_to_name": doc.name,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()  # Penting agar notifikasi langsung tersimpan


def get_users_with_role(role_name):
	"""Mengambil daftar user yang memiliki role tertentu."""
	users = frappe.get_all("Has Role", filters={"role": role_name, "parenttype": "User"}, fields=["parent"])
	return [user.parent for user in users]
