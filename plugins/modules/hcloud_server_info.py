#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Hetzner Cloud GmbH <info@hetzner-cloud.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: hcloud_server_info

short_description: Gather infos about your Hetzner Cloud servers.


description:
    - Gather infos about your Hetzner Cloud servers.
    - This module was called C(hcloud_server_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_server_facts).
      Note that the M(hetzner.hcloud.hcloud_server_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_server_info)!

author:
    - Lukas Kaemmerling (@LKaemmerling)

options:
    id:
        description:
            - The ID of the server you want to get.
        type: int
    name:
        description:
            - The name of the server you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the server you want to get.
        type: str
extends_documentation_fragment:
- hetzner.hcloud.hcloud

'''

EXAMPLES = """
- name: Gather hcloud server infos
  hcloud_server_info:
  register: output

- name: Print the gathered infos
  debug:
    var: output.hcloud_server_info
"""

RETURN = """
hcloud_server_info:
    description: The server infos as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the server
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the server
            returned: always
            type: str
            sample: my-server
        status:
            description: Status of the server
            returned: always
            type: str
            sample: running
        server_type:
            description: Name of the server type of the server
            returned: always
            type: str
            sample: cx11
        ipv4_address:
            description: Public IPv4 address of the server
            returned: always
            type: str
            sample: 116.203.104.109
        ipv6:
            description: IPv6 network of the server
            returned: always
            type: str
            sample: 2a01:4f8:1c1c:c140::/64
        private_networks:
            description: List of private networks the server is attached to (name)
            returned: always
            type: list
            elements: str
            sample: ['my-network', 'another-network']
        private_networks_info:
            description: List of private networks the server is attached to (dict with name and ip)
            returned: always
            type: list
            elements: dict
            sample: [{'name': 'my-network', 'ip': '192.168.1.1'}, {'name': 'another-network', 'ip': '10.185.50.40'}]
        location:
            description: Name of the location of the server
            returned: always
            type: str
            sample: fsn1
        placement_group:
            description: Placement Group of the server
            type: str
            returned: always
            sample: 4711
            version_added: "1.5.0"
        datacenter:
            description: Name of the datacenter of the server
            returned: always
            type: str
            sample: fsn1-dc14
        rescue_enabled:
            description: True if rescue mode is enabled, Server will then boot into rescue system on next reboot
            returned: always
            type: bool
            sample: false
        backup_window:
            description: Time window (UTC) in which the backup will run, or null if the backups are not enabled
            returned: always
            type: bool
            sample: 22-02
        labels:
            description: User-defined labels (key-value pairs)
            returned: always
            type: dict
        delete_protection:
            description: True if server is protected for deletion
            type: bool
            returned: always
            sample: false
            version_added: "0.1.0"
        rebuild_protection:
            description: True if server is protected for rebuild
            type: bool
            returned: always
            sample: false
            version_added: "0.1.0"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.hetzner.hcloud.plugins.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    APIException = None


class AnsibleHcloudServerInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_server_info")
        self.hcloud_server_info = None

    def _prepare_result(self):
        tmp = []

        for server in self.hcloud_server_info:
            if server is not None:
                image = None if server.image is None else to_native(server.image.name)
                placement_group = None if server.placement_group is None else to_native(server.placement_group.name)
                ipv4_address = None if server.public_net.ipv4 is None else to_native(server.public_net.ipv4.ip)
                ipv6 = None if server.public_net.ipv6 is None else to_native(server.public_net.ipv6.ip)
                backup_window = None if server.backup_window is None else to_native(server.backup_window)
                tmp.append({
                    "id": to_native(server.id),
                    "name": to_native(server.name),
                    "ipv4_address": ipv4_address,
                    "ipv6": ipv6,
                    "private_networks": [to_native(net.network.name) for net in server.private_net],
                    "private_networks_info": [{"name": to_native(net.network.name), "ip": net.ip} for net in server.private_net],
                    "image": image,
                    "server_type": to_native(server.server_type.name),
                    "datacenter": to_native(server.datacenter.name),
                    "location": to_native(server.datacenter.location.name),
                    "placement_group": placement_group,
                    "rescue_enabled": server.rescue_enabled,
                    "backup_window": backup_window,
                    "labels": server.labels,
                    "status": to_native(server.status),
                    "delete_protection": server.protection["delete"],
                    "rebuild_protection": server.protection["rebuild"],
                })
        return tmp

    def get_servers(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_server_info = [self.client.servers.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_server_info = [self.client.servers.get_by_name(
                    self.module.params.get("name")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_server_info = self.client.servers.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_server_info = self.client.servers.get_all()

        except Exception as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                label_selector={"type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudServerInfo.define_module()

    is_old_facts = module._name == 'hcloud_server_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_server_facts' module has been renamed to 'hcloud_server_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.0.0', collection_name="hetzner.hcloud")

    hcloud = AnsibleHcloudServerInfo(module)
    hcloud.get_servers()
    result = hcloud.get_result()

    if is_old_facts:
        ansible_info = {
            'hcloud_server_facts': result['hcloud_server_info']
        }
        module.exit_json(ansible_facts=ansible_info)
    else:
        ansible_info = {
            'hcloud_server_info': result['hcloud_server_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
