<template>
	<div class="p-5">
		<div v-if="!$resources.upcomingInvoice.loading">
			<div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
				<div class="rounded-md border p-4">
					<div class="flex items-center justify-between">
						<div class="mb-2 text-sm text-gray-700">Current Billing Amount</div>
						<Button @click="showUpcomingInvoiceDialog = true"> Details </Button>
					</div>
					<div class="text-lg font-medium">
						{{ upcomingInvoice ? upcomingInvoice.formatted.total : '0.00' }}
					</div>
				</div>
				<div class="rounded-md border p-4">
					<div class="flex justify-between text-sm text-gray-700">
						<div class="mb-2">Unpaid Amount</div>
						<Button
							@click="showPrepaidCreditsDialog = true"
							theme="gray"
							iconLeft="credit-card"
						>
							Pay
						</Button>
					</div>
					<div class="text-lg font-medium">
						{{
							($team.doc.currency == 'INR' ? '₹' : '$') +
							' ' +
							Math.ceil($resources.unpaidAmountDue.data)
						}}
					</div>
				</div>
				<div class="rounded-md border p-4">
					<div class="flex justify-between text-sm text-gray-700">
						<div class="mb-2">Account Balance</div>
						<Button
							@click="showPrepaidCreditsDialog = true"
							theme="gray"
							iconLeft="plus"
							>Add</Button
						>
					</div>
					<div class="text-lg font-medium">
						{{ availableCredits }}
					</div>
				</div>

				<div class="rounded-md border p-4">
					<div class="flex justify-between text-sm text-gray-700">
						<div class="mb-2">Payment Mode</div>
						<Button @click="showChangeModeDialog = true"> Change </Button>
					</div>
					<div class="text-lg font-medium">
						{{ $team.doc.payment_mode || 'Not set' }}
					</div>
				</div>
				<div class="border rounded-md p-4">
						<div class="flex justify-between text-base">
							<div>Coupon Code</div>
							<Button @click="send_data()" theme="gray"
								>Apply</Button
							>
						</div>
						<div class="text-2xl font-medium">
							<input type="text" id="coupon_code" class="styled-input">
						</div>
						<span id="coupon_message"></span>
					</div>
				<div class="rounded-md border p-4">
					<div class="flex justify-between text-sm text-gray-700">
						<div class="mb-2">Billing Details</div>
						<Button @click="showBillingDetailsDialog = true"> Update </Button>
					</div>
					<div class="overflow-hidden text-ellipsis text-base font-medium">
						<span class="whitespace-nowrap" v-if="$team.doc.billing_details">
							{{ billingDetailsSummary }}
						</span>
						<span v-else class="font-normal text-gray-600">Not set</span>
					</div>
				</div>
				<div class="rounded-md border p-4">
					<div class="flex justify-between text-sm text-gray-700">
						<div class="mb-2">Payment Method</div>
						<Button @click="showAddCardDialog = true">
							{{ $team.doc.payment_method ? 'Change' : 'Add' }}
						</Button>
					</div>
					<div class="overflow-hidden text-ellipsis text-base font-medium">
						<div v-if="$team.doc.payment_method">
							{{ $team.doc.payment_method.name_on_card }}
							<span class="text-gray-500">••••</span>
							{{ $team.doc.payment_method.last_4 }}
							&middot;
							<span class="font-normal text-gray-600">
								Expiry {{ $team.doc.payment_method.expiry_month }}/{{
									$team.doc.payment_method.expiry_year
								}}
							</span>
						</div>

						<span v-else class="font-normal text-gray-600">Not set</span>
					</div>
				</div>
			</div>

			<!-- <div class="mt-1">
				<a
					href="https://frappecloud.com/payment-options"
					target="_blank"
					class="text-sm text-gray-700 underline"
				>
					Alternative Payment Options
				</a>
			</div> -->
		</div>

		<div class="py-20 text-center" v-if="$resources.upcomingInvoice.loading">
			<Button :loading="true" loadingText="Loading" />
		</div>

		<ChangePaymentModeDialog2 v-model="showChangeModeDialog" />

		<BuyPrepaidCreditsDialog
			v-if="showPrepaidCreditsDialog"
			v-model="showPrepaidCreditsDialog"
			:minimumAmount="minimumAmount"
			@success="
				() => {
					$resources.upcomingInvoice.reload();
					showPrepaidCreditsDialog = false;
				}
			"
		/>

		<UpdateBillingDetails
			v-model="showBillingDetailsDialog"
			@updated="
				showBillingDetailsDialog = false
				// $resources.billingDetails.reload();
			"
		/>

		<StripeCardDialog v-model="showAddCardDialog" />

		<Dialog
			v-if="upcomingInvoice?.name"
			v-model="showUpcomingInvoiceDialog"
			:options="{ title: 'Total usage for this month', size: '3xl' }"
		>
			<template #body-content>
				<InvoiceTable :invoiceId="upcomingInvoice.name" />
			</template>
		</Dialog>
	</div>
</template>
<script>
import { defineAsyncComponent } from 'vue';
import InvoiceTable from '../components/InvoiceTable.vue';
import UpdateBillingDetails from '@/components/UpdateBillingDetails.vue';

export default {
	name: 'BillingOverview',
	components: {
		InvoiceTable,
		UpdateBillingDetails,
		ChangePaymentModeDialog2: defineAsyncComponent(() =>
			import('../components/ChangePaymentModeDialog.vue')
		),
		BuyPrepaidCreditsDialog: defineAsyncComponent(() =>
			import('../components/BuyPrepaidCreditsDialog.vue')
		),
		StripeCardDialog: defineAsyncComponent(() =>
			import('../components/StripeCardDialog.vue')
		)
	},
	resources: {
		upcomingInvoice: { url: 'press.api.billing.upcoming_invoice', auto: true },
		unpaidAmountDue() {
			return {
				url: 'press.api.billing.total_unpaid_amount',
				auto: true
			};
		}
	},
	data() {
		return {
			showPrepaidCreditsDialog: false,
			showChangeModeDialog: false,
			showBillingDetailsDialog: false,
			showAddCardDialog: false,
			showUpcomingInvoiceDialog: false,
			error: null,
			success: null,
		};
	},
	mounted() {
		this.$socket.on('balance_updated', () =>
			this.$resources.upcomingInvoice.reload()
		);
	},
	beforeUnmount() {
		this.$socket.off('balance_updated');
	},
	computed: {
		minimumAmount() {
			const unpaidAmount = this.$resources.unpaidAmountDue.data;
			const minimumDefault = this.$team.doc.currency == 'INR' ? 800 : 10;

			return Math.ceil(
				unpaidAmount && unpaidAmount > minimumDefault
					? unpaidAmount
					: minimumDefault
			);
		},
		upcomingInvoice() {
			return this.$resources.upcomingInvoice.data?.upcoming_invoice;
		},
		availableCredits() {
			return this.$resources.upcomingInvoice.data?.available_credits;
		},
		billingDetailsSummary() {
			const billingDetails = this.$team.doc.billing_details;
			if (!billingDetails) {
				return '';
			}

			const {
				billing_name,
				address_line1,
				country,
				city,
				state,
				pincode,
				gstin
			} = billingDetails;

			return [billing_name, address_line1, city, state, country, pincode, gstin]
				.filter(Boolean)
				.join(', ');
		}
	},
	methods:{
		send_data() {
			let coupon_code = document.getElementById("coupon_code").value;
			fetch('/api/method/press.api.coupon.check_coupan', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					coupon_code: coupon_code
				})
			})
			.then(response => response.json())
			.then(data => {
				let message = document.getElementById("coupon_message");
				message.innerText = data.message;
				if(data.message == "Unlimited Coupon Applied"){
					message.classList.add("success");
				}
				else{
					message.classList.add("error");
				}
				window.location.reload();
			})
		},
	}
};
</script>

<style>
	.error{
		color:red;
	}
	.success{
		color:green;
	}
	.styled-input {
    background-color: #f0f0f0; /* Light grey background */
    border: 1px solid #ccc;    /* Light grey border */
    border-radius: 4px;        /* Rounded corners */
    padding: 10px;             /* Padding inside the input */
    font-size: 16px;           /* Font size */
    width: 65%;               /* Full width */
    box-sizing: border-box;    /* Ensures padding doesn't exceed the width */
    transition: all 0.3s ease; /* Smooth transition for focus effect */
}
	.styled-input:focus {
		border-color: #888;        /* Darker grey border on focus */
		outline: none;             /* Remove default outline */
		box-shadow: 0 0 5px rgba(0, 0, 0, 0.2); /* Subtle shadow on focus */
	}
</style>
