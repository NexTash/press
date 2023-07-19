# Copyright (c) 2023, Frappe and Contributors
# See license.txt


from unittest.mock import Mock, patch
from press.press.doctype.ansible_play.test_ansible_play import create_test_ansible_play

from press.press.doctype.self_hosted_server.self_hosted_server import SelfHostedServer
import frappe
import json
from press.runner import Ansible
from press.press.doctype.team.test_team import create_test_team
from frappe.tests.utils import FrappeTestCase


class TestSelfHostedServer(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_autoname_to_fqdn(self):
		hostnames = ["a1", "a1.b1", "waaaaaaawwwaawwa", "1234561234"]
		for host in hostnames:
			server = create_test_self_hosted_server(host)
			self.assertEqual(server.name, f"{host}.fc.dev")

	@patch(
		"press.press.doctype.self_hosted_server.self_hosted_server.Ansible",
		wraps=Ansible,
	)
	@patch.object(Ansible, "run", new=Mock())
	def test_setup_nginx_triggers_nginx_ssl_playbook(self, Mock_Ansible: Mock):
		server = create_test_self_hosted_server("ssl")
		server.setup_nginx()
		Mock_Ansible.assert_called_with(
			playbook="self_hosted_nginx.yml",
			server=server,
			user=server.ssh_user or "root",
			port=server.ssh_port or "22",
			variables={"domain": server.name},
		)

	def test_setup_nginx_creates_tls_certificate_post_success(self):
		server = create_test_self_hosted_server("ssl")
		pre_setup_count = frappe.db.count("TLS Certificate")
		with patch(
			"press.press.doctype.self_hosted_server.self_hosted_server.Ansible.run",
			new=lambda x: create_test_ansible_play(
				"Setup Self Hosted Nginx",
				"self_hosted_nginx.yml",
				server.doctype,
				server.name,
				{"server": "ssl.fc.dev"},
			),
		):
			server.create_tls_certs()
		post_setup_count = frappe.db.count("TLS Certificate")
		self.assertEqual(pre_setup_count, post_setup_count - 1)

	def test_successful_ping_ansible_sets_status_to_pending(self):
		server = create_test_self_hosted_server("pinger")
		with patch(
			"press.press.doctype.self_hosted_server.self_hosted_server.Ansible.run",
			new=lambda x: create_test_ansible_play(
				"Ping Server",
				"ping.yml",
				server.doctype,
				server.name,
				{"server": server.name},
			),
		):
			server.ping_ansible()
		self.assertEqual(server.status, "Pending")

	def test_failed_ping_ansible_sets_status_to_unreachable(self):
		server = create_test_self_hosted_server("pinger")
		with patch(
			"press.press.doctype.self_hosted_server.self_hosted_server.Ansible.run",
			new=lambda x: create_test_ansible_play(
				"Ping Server",
				"ping.yml",
				server.doctype,
				server.name,
				{"server": server.name},
				"Failure",
			),
		):
			server.ping_ansible()
		self.assertEqual(server.status, "Unreachable")

	def test_get_apps_populates_apps_child_table(self):
		server = create_test_self_hosted_server("apps")
		with patch(
			"press.press.doctype.self_hosted_server.self_hosted_server.Ansible.run",
			new=lambda x: _create_test_ansible_play_and_task(
				server=server,
				playbook="get_apps.yml",
				_play="Get Bench data from Self Hosted Server",
				task_1="Get Versions from Current Bench",
				task_1_output=json.dumps(
					[
						{
							"commit": "3672c9f",
							"app": "frappe",
							"branch": "version-14",
							"version": "14.30.0",
						}
					]
				),
				task_1_result="",
			),
		):
			server._get_apps()
		server.reload()
		self.assertTrue(server.apps)
		self.assertEqual(len(server.apps), 1)
		self.assertEqual(server.apps[0].app_name, "frappe")
		self.assertEqual(server.apps[0].branch, "version-14")
		self.assertEqual(server.apps[0].version, "14.30.0")

	def test_get_sites_populates_site_table_with_config(self):
		server = create_test_self_hosted_server("sites")
		server.bench_path = "/home/frappe/frappe-bench"
		with patch(
			"press.press.doctype.self_hosted_server.self_hosted_server.Ansible.run",
			new=lambda x: _create_test_ansible_play_and_task(
				server=server,
				playbook="get_sites.yml",
				_play="Sites from Current Bench",
				task_1="Get Sites from Current Bench",
				task_1_output=json.dumps({"site1.local": ["frappe", "erpnext"]}),
				task_1_result="",
				task_2="Get Site Configs from Existing Sites",
				task_2_output=json.dumps(
					[
						{
							"site": "site1.local",
							"config": {
								"activations_last_sync_date": "2023-05-07 00:00:49.152290",
								"always_use_account_email_id_as_sender": 1,
							},
						}
					]
				),
				task_2_result="",
			),
		):
			server._get_sites()
		server.reload()
		self.assertTrue(server.sites)
		self.assertTrue(server.sites[0].site_config)
		self.assertEqual(len(server.sites), 1)
		self.assertEqual(
			server.sites[0].site_config,
			json.dumps(
				{
					"activations_last_sync_date": "2023-05-07 00:00:49.152290",
					"always_use_account_email_id_as_sender": 1,
				}
			),
		)
		self.assertEqual(server.sites[0].apps, "frappe,erpnext")

	def test_fetch_system_ram_from_ansible_and_update_ram_field(self):
		server = create_test_self_hosted_server("ram")
		_create_test_ansible_play_and_task(
			server=server,
			playbook="ping.yml",
			_play="Ping Server",
			task_1="Gather Facts",
			task_1_output="",
			task_1_result='{"ansible_facts": {"memtotal_mb": 16384}}',
		)
		server.fetch_system_ram()
		server.reload()
		self.assertEqual(server.ram, "16384")


def create_test_self_hosted_server(host) -> SelfHostedServer:
	server = frappe.get_doc(
		{
			"doctype": "Self Hosted Server",
			"ip": frappe.mock("ipv4"),
			"private_ip": frappe.mock("ipv4_private"),
			"server_url": f"https://{host}.fc.dev",
			"team": create_test_team().name,
		}
	).insert(ignore_if_duplicate=True)
	server.reload()
	return server


def _create_test_ansible_play_and_task(
	server: SelfHostedServer, playbook: str, _play: str, **kwargs
):  # TODO: Move to AnsiblePlay and Make a generic one for AnsibleTask
	play = create_test_ansible_play(
		_play,
		playbook,
		server.doctype,
		server.name,
		{"server": server.name},
	)

	for i, _ in enumerate(kwargs):
		try:
			task = frappe.get_doc(
				{
					"doctype": "Ansible Task",
					"status": "Success",
					"play": play.name,
					"role": play.playbook.split(".")[0],
					"task": kwargs.get("task_" + str(i + 1)),
					"output": kwargs.get("task_" + str(i + 1) + "_output"),
					"result": kwargs.get("task_" + str(i + 1) + "_result"),
				}
			)
			task.insert()
		except:
			pass
	return play
