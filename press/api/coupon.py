import frappe
from datetime import datetime

@frappe.whitelist()
def check_coupan(coupon_code):
	team = get_current_team(get_doc=True)
	frappe.flags.ignore_permissions = True
	if frappe.db.exists("Coupon Code", {'coupon_code': coupon_code, "custom_unlimited_coupon" : 1}):
		team.db_set("custom_is_unlimited_coupon_used", 1)
		frappe.db.commit()
		return "Unlimited Coupon Applied"
	else:
		return "Invalid Coupon"
    
# @frappe.whitelist(allow_guest = True)
# def apply_discount(coupon_code):
#     if frappe.db.exists("Coupon Code", {'coupon_code': coupon_code, "custom_discount_coupon": 1}):
#         value = frappe.db.get_value("Coupon Code", {'coupon_code': coupon_code, "custom_discount_coupon": 1}, "custom_discount")
#         return value


def get_current_team(get_doc=False):
	if frappe.session.user == "Guest":
		frappe.throw("Not Permitted", frappe.PermissionError)

	if not hasattr(frappe.local, "request"):
		# if this is not a request, send the current user as default team
		# always use parent_team for background jobs
		return (
			frappe.get_doc(
				"Team",
				{"user": frappe.session.user, "enabled": 1, "parent_team": ("is", "not set")},
			)
			if get_doc
			else frappe.get_value(
				"Team",
				{"user": frappe.session.user, "enabled": 1, "parent_team": ("is", "not set")},
				"name",
			)
		)

	system_user = frappe.session.data.user_type == "System User"

	# get team passed via request header
	team = frappe.get_request_header("X-Press-Team")

	user_is_press_admin = frappe.db.exists(
		"Has Role", {"parent": frappe.session.user, "role": "Press Admin"}
	)

	if (
		not team
		and user_is_press_admin
		and frappe.db.exists("Team", {"user": frappe.session.user})
	):
		# if user has_role of Press Admin then just return current user as default team
		return (
			frappe.get_doc("Team", {"user": frappe.session.user, "enabled": 1})
			if get_doc
			else frappe.get_value("Team", {"user": frappe.session.user, "enabled": 1}, "name")
		)

	if not team:
		# if team is not passed via header, get the default team for user
		team = get_default_team_for_user(frappe.session.user)

	if not system_user and not is_user_part_of_team(frappe.session.user, team):
		# if user is not part of the team, get the default team for user
		team = get_default_team_for_user(frappe.session.user)
		if not team:
			frappe.throw(
				"User {0} does not belong to Team {1}".format(frappe.session.user, team),
				frappe.PermissionError,
			)

	if not frappe.db.exists("Team", {"name": team, "enabled": 1}):
		frappe.throw("Invalid Team", frappe.PermissionError)

	if get_doc:
		return frappe.get_doc("Team", team)

	return team

def get_default_team_for_user(user):
	"""Returns the Team if user has one, or returns the Team in which they belong"""
	if frappe.db.exists("Team", {"user": user, "enabled": 1}):
		return frappe.db.get_value("Team", {"user": user, "enabled": 1}, "name")

	teams = frappe.db.get_values(
		"Team Member",
		filters={"parenttype": "Team", "user": user},
		fieldname="parent",
		pluck="parent",
	)
	for team in teams:
		# if user is part of multiple teams, send the first enabled one
		if frappe.db.exists("Team", {"name": team, "enabled": 1}):
			return team
		
def is_user_part_of_team(user, team):
	"""Returns True if user is part of the team"""
	return frappe.db.exists(
		"Team Member", {"parenttype": "Team", "parent": team, "user": user}
	)