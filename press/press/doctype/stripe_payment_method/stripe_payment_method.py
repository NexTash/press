# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from press.api.billing import get_stripe
from frappe.contacts.address_and_contact import load_address_and_contact
from press.overrides import get_permission_query_conditions_for_doctype


class StripePaymentMethod(Document):
	def onload(self):
		load_address_and_contact(self)

	def set_default(self):
		stripe = get_stripe()
		# set default payment method on stripe
		stripe.Customer.modify(
			self.stripe_customer_id,
			invoice_settings={"default_payment_method": self.stripe_payment_method_id},
		)
		frappe.db.update(
			"Stripe Payment Method",
			{"team": self.team, "name": ("!=", self.name)},
			"is_default",
			0,
		)
		self.is_default = 1
		self.save()
		frappe.db.set_value("Team", self.team, "default_payment_method", self.name)

	def on_trash(self):
		payment_methods = frappe.db.get_all(
			"Stripe Payment Method", filters={"team": self.team}, limit=2
		)
		if len(payment_methods) == 1:
			frappe.throw("Cannot delete the only payment method")

	def after_delete(self):
		if self.is_default:
			frappe.throw("Cannot delete default payment method")

		stripe = get_stripe()
		stripe.PaymentMethod.detach(self.stripe_payment_method_id)


get_permission_query_conditions = get_permission_query_conditions_for_doctype(
	"Stripe Payment Method"
)
