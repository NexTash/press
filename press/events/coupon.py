import frappe
from datetime import datetime

@frappe.whitelist(allow_guest = True)
def check_coupan(coupon_code):
    if frappe.db.exists("Coupon Code", {'coupon_code': coupon_code}):
        current_date = datetime.now().date()
        # if frappe.db.exists("Coupon Code", {current_date : ["<", valid_from]}):
        return "Existed"
    else:
        return "Invalid Coupon Code"