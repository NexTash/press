<template>
	<div class="sticky top-0 z-10 shrink-0">
		<Header>
			<Breadcrumbs
				:items="[
					{ label: 'Servers', route: '/servers' },
					{ label: 'New Server', route: '/servers/new' },
				]"
			/>
		</Header>
	</div>

	<div
		v-if="!$team.doc?.is_desk_user && !$session.hasServerCreationAccess"
		class="mx-auto mt-60 w-fit rounded border border-dashed px-12 py-8 text-center text-gray-600"
	>
		<i-lucide-alert-triangle class="mx-auto mb-4 h-6 w-6 text-red-600" />
		<ErrorMessage message="You aren't permitted to create new servers" />
	</div>

	<div v-else-if="serverEnabled" class="mx-auto max-w-2xl px-5">
		<div v-if="options" class="space-y-12 pb-[50vh] pt-12">
			<div class="flex flex-col">
				<h2 class="text-sm font-medium leading-6 text-gray-900">
					Choose Server Type
				</h2>
				<div class="mt-2 w-full space-y-2">
					<div class="grid grid-cols-2 gap-3">
						<button
							v-for="c in options?.server_types"
							:key="c.name"
							@click="serverType = c.name"
							:class="[
								serverType === c.name
									? 'border-gray-900 ring-1 ring-gray-900 hover:bg-gray-100'
									: 'border-gray-400 bg-white text-gray-900 ring-gray-200 hover:bg-gray-50',
								'flex w-full items-center rounded border p-3 text-left text-base text-gray-900',
							]"
						>
							<div class="flex w-full items-center justify-between space-x-2">
								<span class="text-sm font-medium">
									{{ c.title }}
								</span>
								<Tooltip :text="c.description">
									<i-lucide-info class="h-4 w-4 text-gray-500" />
								</Tooltip>
							</div>
						</button>
					</div>
				</div>
			</div>
			<div v-if="serverType" class="flex flex-col">
				<h2 class="text-sm font-medium leading-6 text-gray-900">
					Enter Server Name
				</h2>
				<div class="mt-2">
					<FormControl
						v-model="serverTitle"
						type="text"
						class="block rounded-md border-gray-300 shadow-sm focus:border-gray-900 focus:ring-gray-900 sm:text-sm"
					/>
				</div>
			</div>
			<div v-if="serverType === 'dedicated'" class="space-y-12">
				<div class="flex flex-col" v-if="options?.regions.length">
					<h2 class="text-sm font-medium leading-6 text-gray-900">
						Select Region
					</h2>
					<div class="mt-2 w-full space-y-2">
						<div class="grid grid-cols-2 gap-3">
							<button
								v-for="c in options?.regions"
								:key="c.name"
								@click="serverRegion = c.name"
								:class="[
									serverRegion === c.name
										? 'border-gray-900 ring-1 ring-gray-900 hover:bg-gray-100'
										: 'border-gray-400 bg-white text-gray-900 ring-gray-200 hover:bg-gray-50',
									'flex w-full items-center rounded border p-3 text-left text-base text-gray-900',
								]"
							>
								<div class="flex w-full items-center justify-between">
									<div class="flex w-full items-center space-x-2">
										<img :src="c.image" class="h-5 w-5" />
										<span class="text-sm font-medium">
											{{ c.title }}
										</span>
									</div>
									<Badge v-if="c.beta" :label="c.beta ? 'Beta' : ''" />
								</div>
							</button>
						</div>
					</div>
				</div>
				<div
					v-if="serverRegion && options.app_premium_plans.length > 0"
					class="flex flex-col"
				>
					<div class="flex items-center justify-between">
						<h2 class="text-sm font-medium leading-6 text-gray-900">
							Plan Type
						</h2>
						<div>
							<Button
								link="https://frappecloud.com/pricing#dedicated"
								variant="ghost"
							>
								<template #prefix>
									<i-lucide-help-circle class="h-4 w-4 text-gray-700" />
								</template>
								Help
							</Button>
						</div>
					</div>
					<div class="mt-2 w-full space-y-2">
						<div class="grid grid-cols-2 gap-3">
							<button
								v-for="c in [
									{
										name: 'Standard',
										description: 'Includes standard support and SLAs',
									},
									{
										name: 'Premium',
										description: 'Includes enterprise support and SLAs',
									},
								]"
								:key="c.name"
								@click="planType = c.name"
								:class="[
									planType === c.name
										? 'border-gray-900 ring-1 ring-gray-900 hover:bg-gray-100'
										: 'border-gray-400 bg-white text-gray-900 ring-gray-200 hover:bg-gray-50',
									'flex w-full items-center rounded border p-3 text-left text-base text-gray-900',
								]"
							>
								<div class="flex w-full items-center justify-between space-x-2">
									<span class="text-sm font-medium">
										{{ c.name }}
									</span>
									<Tooltip :text="c.description">
										<i-lucide-info class="h-4 w-4 text-gray-500" />
									</Tooltip>
								</div>
							</button>
						</div>
					</div>
				</div>
				<div v-if="serverRegion">
					<div class="flex flex-col" v-if="options?.app_plans.length">
						<h2 class="text-sm font-medium leading-6 text-gray-900">
							Select Application Server Plan
						</h2>
						<div class="mt-2 space-y-2">
							<ServerPlansCards
								v-model="appServerPlan"
								:plans="
									(planType === 'Standard'
										? options.app_plans
										: options.app_premium_plans
									).filter((p) => {
										const isARMSupportedCluster =
											p.cluster === 'Mumbai' || p.cluster === 'Frankfurt';
										return (
											p.cluster === serverRegion &&
											(!isARMSupportedCluster || p.platform === 'arm64')
										);
									})
								"
							/>
						</div>
					</div>
				</div>
				<div v-if="serverRegion">
					<div class="flex flex-col" v-if="options?.db_plans.length">
						<h2 class="text-sm font-medium leading-6 text-gray-900">
							Select Database Server Plan
						</h2>
						<div class="mt-2 w-full space-y-2">
							<ServerPlansCards
								v-if="options.db_plans"
								v-model="dbServerPlan"
								:plans="
									(planType === 'Standard'
										? options.db_plans
										: options.db_premium_plans
									).filter((p) => {
										const isARMSupportedCluster =
											p.cluster === 'Mumbai' || p.cluster === 'Frankfurt';
										return (
											p.cluster === serverRegion &&
											(!isARMSupportedCluster || p.platform === 'arm64')
										);
									})
								"
							/>
						</div>
					</div>
				</div>
			</div>
			<div v-else-if="serverType === 'hybrid'" class="space-y-12">
				<div class="flex flex-col space-y-2">
					<h2 class="text-sm font-medium leading-6 text-gray-900">
						App Server IP Addresses
					</h2>
					<div class="flex space-x-3">
						<FormControl
							class="w-full"
							v-model="appPublicIP"
							label="Public IP"
							type="text"
						/>
						<FormControl
							class="w-full"
							v-model="appPrivateIP"
							label="Private IP"
							type="text"
						/>
					</div>
				</div>
				<div class="flex flex-col space-y-2">
					<h2 class="text-sm font-medium leading-6 text-gray-900">
						Database Server IP Addresses
					</h2>
					<div class="flex space-x-3">
						<FormControl
							class="w-full"
							v-model="dbPublicIP"
							label="Public IP"
							type="text"
						/>
						<FormControl
							class="w-full"
							v-model="dbPrivateIP"
							label="Private IP"
							type="text"
						/>
					</div>
				</div>
				<div class="flex flex-col space-y-2">
					<h2 class="text-sm font-medium leading-6 text-gray-900">
						Add SSH Key
					</h2>
					<span class="text-xs text-gray-600">
						Add this SSH Key to
						<span class="font-mono">~/.ssh/authorized_keys</span>
						file on Application and Database server</span
					>
					<ClickToCopy :textContent="$resources.hybridOptions.data.ssh_key" />
				</div>
			</div>
			<div
				class="flex flex-col space-y-3"
				v-if="serverType === 'dedicated' && serverRegion"
			>
				<h2 class="text-base font-medium leading-6 text-gray-900">
					Auto Add-on Storage
				</h2>
				<div class="my-4 rounded border bg-gray-50 p-2 prose-sm prose">
					This feature will automatically increases the storage as it reaches
					over <b>90%</b> of its capacity.

					<br /><br />
					With this feature disabled, disk capacity
					<strong>will not increase automatically</strong> in the event your
					server approaches or reaches its storage limit.

					<br /><br />
					<strong>Note :</strong>

					<ul>
						<li v-if="this.storagePlanRate">
							• You will be charged at the rate of
							<b>{{ this.$format.userCurrency(this.storagePlanRate) }}/mo</b>
							for each additional GB of storage.
						</li>

						<li>
							• Disabling this feature may result in
							<strong>service degradation or downtime</strong> if storage is
							exhausted.
						</li>

						<li>
							• Storage can auto increase only once in <strong>6 hours</strong>.
						</li>
					</ul>
				</div>
				<div>
					<FormControl
						type="checkbox"
						v-model="enableAutoAddStorage"
						label="Enable Auto Add-on Storage for Application and Database Server"
					/>
				</div>
			</div>

			<Summary
				:options="summaryOptions"
				v-if="
					serverTitle &&
					((serverRegion && dbServerPlan && appServerPlan) ||
						(appPublicIP && appPrivateIP && dbPublicIP && dbPrivateIP))
				"
			/>
			<div
				class="flex flex-col space-y-4"
				v-if="
					serverTitle &&
					((serverRegion && dbServerPlan && appServerPlan) ||
						(appPublicIP && appPrivateIP && dbPublicIP && dbPrivateIP))
				"
			>
				<FormControl
					type="checkbox"
					v-model="agreedToRegionConsent"
					:label="`I agree that the laws of the region selected by me shall stand applicable to me and Frappe.`"
				/>
				<ErrorMessage
					class="my-2"
					:message="
						$resources.createServer.error || $resources.createHybridServer.error
					"
				/>
				<Button
					variant="solid"
					:disabled="!agreedToRegionConsent"
					@click="
						serverType === 'dedicated'
							? $resources.createServer.submit({
									server: {
										title: serverTitle,
										cluster: serverRegion,
										app_plan: appServerPlan?.name,
										db_plan: dbServerPlan?.name,
										auto_increase_storage: enableAutoAddStorage,
									},
								})
							: $resources.createHybridServer.submit({
									server: {
										title: serverTitle,
										app_public_ip: appPublicIP,
										app_private_ip: appPrivateIP,
										db_public_ip: dbPublicIP,
										db_private_ip: dbPrivateIP,
										plan: $resources.hybridOptions.data.plans[0],
									},
								})
					"
					:loading="
						$resources.createServer.loading ||
						$resources.createHybridServer.loading
					"
				>
					{{ serverType === 'hybrid' ? 'Add Hybrid Server' : 'Create Server' }}
				</Button>
			</div>
		</div>
	</div>
	<div
		v-else
		class="mx-auto mt-60 w-fit rounded border-2 border-dashed px-12 py-8 text-center text-gray-600"
	>
		<LucideServer class="mx-auto mb-4 h-8 w-8" />
		<p>Server feature isn't enabled for your account.</p>
		<p>You need to have $200 worth of credits to enable this feature.</p>
		<p>
			Please add it from
			<router-link class="underline" :to="{ name: 'BillingOverview' }"
				>here</router-link
			>.
		</p>
		<p>
			Or you can
			<a
				class="underline"
				href="https://frappecloud.com/support"
				target="_blank"
				>contact support</a
			>
			to enable it.
		</p>
	</div>
</template>
<script>
import LucideServer from '~icons/lucide/server-off';
import Header from '../components/Header.vue';
import Summary from '../components/Summary.vue';
import ServerPlansCards from '../components/server/ServerPlansCards.vue';
import ClickToCopy from '../components/ClickToCopyField.vue';
import { DashboardError } from '../utils/error';

export default {
	components: {
		ServerPlansCards,
		LucideServer,
		ClickToCopy,
		Summary,
		Header,
	},
	props: ['server'],
	data() {
		return {
			serverTitle: '',
			appServerPlan: '',
			dbServerPlan: '',
			serverRegion: '',
			serverType: '',
			appPublicIP: '',
			appPrivateIP: '',
			dbPublicIP: '',
			dbPrivateIP: '',
			planType: 'Standard',
			serverEnabled: true,
			enableAutoAddStorage: false,
			agreedToRegionConsent: false,
		};
	},
	watch: {
		serverType() {
			this.appServerPlan = '';
			this.dbServerPlan = '';
			this.serverRegion = '';
			this.appPublicIP = '';
			this.appPrivateIP = '';
			this.dbPublicIP = '';
			this.dbPrivateIP = '';
		},
		planType() {
			this.appServerPlan = '';
			this.dbServerPlan = '';
		},
	},
	resources: {
		options() {
			return {
				url: 'press.api.server.options',
				auto: true,
				transform(data) {
					return {
						server_types: [
							{
								name: 'dedicated',
								title: 'Dedicated Server',
								description:
									'A pair of dedicated servers managed and owned by frappe',
							},
							{
								name: 'hybrid',
								title: 'Hybrid Server',
								description:
									'A pair of dedicated servers managed by frappe and owned/provisioned by you',
							},
						],
						regions: data.regions,
						app_plans: data.app_plans.filter((p) => p.premium == 0),
						db_plans: data.db_plans.filter((p) => p.premium == 0),
						app_premium_plans: data.app_plans.filter((p) => p.premium == 1),
						db_premium_plans: data.db_plans.filter((p) => p.premium == 1),
						storage_plan: data.storage_plan,
					};
				},
				onError(error) {
					if (
						error.messages.includes(
							'Servers feature is not yet enabled on your account',
						)
					) {
						this.serverEnabled = false;
					}
				},
			};
		},
		hybridOptions() {
			return {
				url: 'press.api.selfhosted.options_for_new',
				auto: true,
			};
		},
		createServer() {
			return {
				url: 'press.api.server.new',
				validate({ server }) {
					if (!server.title) {
						throw new DashboardError('Server name is required');
					} else if (!server.cluster) {
						throw new DashboardError('Please select a region');
					} else if (!server.app_plan) {
						throw new DashboardError('Please select an App Server Plan');
					} else if (!server.db_plan) {
						throw new DashboardError('Please select a Database Server Plan');
					} else if (Object.keys(this.$team.doc.billing_details).length === 0) {
						throw new DashboardError(
							"You don't have billing details added. Please add billing details from settings to continue.",
						);
					} else if (
						this.$team.doc.servers_enabled == 0 &&
						((this.$team.doc.currency == 'USD' &&
							this.$team.doc.balance < 200) ||
							(this.$team.doc.currency == 'INR' &&
								this.$team.doc.balance < 16000))
					) {
						throw new DashboardError(
							'You need to have $200 worth of credits to create a server.',
						);
					}
				},
				onSuccess(server) {
					this.$router.push({
						name: 'Server Detail Plays',
						params: { name: server.server },
					});
				},
			};
		},
		createHybridServer() {
			return {
				url: 'press.api.selfhosted.create_and_verify_selfhosted',
				validate() {
					if (!this.serverTitle) {
						throw new DashboardError('Server name is required');
					} else if (
						!this.appPublicIP ||
						!this.dbPublicIP ||
						!this.appPrivateIP ||
						!this.dbPrivateIP
					) {
						throw new DashboardError('Please fill all the IP addresses');
					} else if (this.validateIP(this.appPublicIP)) {
						throw new DashboardError(
							'Please enter a valid Application Public IP',
						);
					} else if (this.validateIP(this.appPrivateIP)) {
						throw new DashboardError(
							'Please enter a valid Application Private IP',
						);
					} else if (this.validateIP(this.dbPublicIP)) {
						throw new DashboardError('Please enter a valid Database Public IP');
					} else if (this.validateIP(this.dbPrivateIP)) {
						throw new DashboardError(
							'Please enter a valid Database Private IP',
						);
					} else if (this.dbPublicIP === this.appPublicIP) {
						throw new DashboardError(
							"Please don't use the same server as Application and Database servers",
						);
					} else if (!this.agreedToRegionConsent) {
						throw new DashboardError('Please agree to the region consent');
					}
				},
				onSuccess(server) {
					this.$router.push({
						name: 'Server Detail Plays',
						params: { name: server },
					});
				},
			};
		},
	},
	computed: {
		options() {
			return this.$resources.options.data;
		},
		_totalPerMonth() {
			let currencyField =
				this.$team.doc.currency == 'INR' ? 'price_inr' : 'price_usd';
			if (this.serverType === 'dedicated') {
				return (
					this.appServerPlan[currencyField] + this.dbServerPlan[currencyField]
				);
			} else if (this.serverType === 'hybrid') {
				return this.$resources.hybridOptions?.data?.plans[0][currencyField] * 2;
			}
		},
		totalPerMonth() {
			return this.$format.userCurrency(this._totalPerMonth);
		},
		totalPerDay() {
			return this.$format.userCurrency(
				this.$format.pricePerDay(this._totalPerMonth),
			);
		},
		summaryOptions() {
			return [
				{
					label: 'Server Name',
					value: this.serverTitle,
				},
				{
					label: 'Region',
					value: this.serverRegion,
					condition: () => this.serverType === 'dedicated',
				},
				{
					label: 'App Server Plan',
					value: this.$format.planTitle(this.appServerPlan) + ' per month',
					condition: () => this.serverType === 'dedicated',
				},
				{
					label: 'DB Server Plan',
					value: this.$format.planTitle(this.dbServerPlan) + ' per month',
					condition: () => this.serverType === 'dedicated',
				},
				{
					label: 'App Public IP',
					value: this.appPublicIP,
					condition: () => this.serverType === 'hybrid',
				},
				{
					label: 'App Private IP',
					value: this.appPrivateIP,
					condition: () => this.serverType === 'hybrid',
				},
				{
					label: 'DB Public IP',
					value: this.dbPublicIP,
					condition: () => this.serverType === 'hybrid',
				},
				{
					label: 'DB Private IP',
					value: this.dbPrivateIP,
					condition: () => this.serverType === 'hybrid',
				},
				{
					label: 'Plan',
					value: `${this.$format.planTitle(
						this.$resources.hybridOptions?.data?.plans[0],
					)} per month`,
					condition: () =>
						this.serverType === 'hybrid' &&
						this.$resources.hybridOptions?.data?.plans[0],
				},
				{
					label: 'Total',
					value: `${this.totalPerMonth} per month <div class="text-gray-600"> ${this.totalPerDay} per day</div>`,
					condition: () => this._totalPerMonth,
				},
			];
		},
		storagePlanRate() {
			if (!this.$team?.doc?.currency) return -1;
			try {
				let priceField =
					this.$team.doc.currency === 'INR' ? 'price_inr' : 'price_usd';
				console.log(this.options);
				return this.options?.storage_plan?.[priceField] || 0;
			} catch (error) {
				return -1;
			}
		},
	},
	methods: {
		validateIP(ip) {
			return !ip.match(
				/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
			);
		},
	},
};
</script>
