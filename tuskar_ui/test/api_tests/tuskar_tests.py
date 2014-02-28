# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import

import contextlib
import mock
from mock import patch  # noqa

from heatclient.v1 import events
from heatclient.v1 import stacks
from novaclient.v1_1 import servers

from tuskar_ui import api
from tuskar_ui.test import helpers as test

# TODO(Tzu-Mainn Chen): uncomment mock data and mock
# api calls once api.py stops using mock data


class TuskarAPITests(test.APITestCase):
    def test_overcloud_create(self):
        overcloud = self.tuskarclient_overclouds.first()
        with patch('tuskarclient.v1.overclouds.OvercloudManager.create',
                   return_value=overcloud):
            ret_val = api.Overcloud.create(self.request, {}, {})
        self.assertIsInstance(ret_val, api.Overcloud)

    def test_overcloud_list(self):
        overclouds = self.tuskarclient_overclouds.list()
        with patch('tuskarclient.v1.overclouds.OvercloudManager.list',
                   return_value=overclouds):
            ret_val = api.Overcloud.list(self.request)
        for oc in ret_val:
            self.assertIsInstance(oc, api.Overcloud)
        self.assertEqual(1, len(ret_val))

    def test_overcloud_get(self):
        overcloud = self.tuskarclient_overclouds.first()
        with patch('tuskarclient.v1.overclouds.OvercloudManager.list',
                   return_value=[overcloud]):
            ret_val = api.Overcloud.get(self.request, overcloud.id)

        self.assertIsInstance(ret_val, api.Overcloud)

    def test_overcloud_delete(self):
        overcloud = self.tuskarclient_overclouds.first()
        with patch('tuskarclient.v1.overclouds.OvercloudManager.delete',
                   return_value=None):
            api.Overcloud.delete(self.request, overcloud.id)

    def test_overcloud_stack(self):
        stack = self.heatclient_stacks.first()
        oc = api.Overcloud(self.tuskarclient_overclouds.first(), request=None)
        with patch('openstack_dashboard.api.heat.stack_get',
                   return_value=stack):
            ret_val = oc.stack
            self.assertIsInstance(ret_val, stacks.Stack)

    def test_overcloud_stack_events(self):
        overcloud = self.tuskarclient_overclouds.first()
        event_list = self.heatclient_events.list()
        stack = self.heatclient_stacks.first()

        with patch('openstack_dashboard.api.heat.stack_get',
                   return_value=stack):
            with patch('openstack_dashboard.api.heat.events_list',
                       return_value=event_list):
                ret_val = api.Overcloud(overcloud).stack_events
        for e in ret_val:
            self.assertIsInstance(e, events.Event)
        self.assertEqual(8, len(ret_val))

    def test_overcloud_stack_events_empty(self):
        overcloud = self.tuskarclient_overclouds.first()
        event_list = self.heatclient_events.list()
        overcloud.stack_id = None

        with patch('openstack_dashboard.api.heat.stack_get',
                   return_value=None):
            with patch('openstack_dashboard.api.heat.events_list',
                       return_value=event_list):
                ret_val = api.Overcloud(overcloud).stack_events

        self.assertListEqual([], ret_val)

    def test_overcloud_is_deployed(self):
        stack = self.heatclient_stacks.first()
        oc = api.Overcloud(self.tuskarclient_overclouds.first(), request=None)
        with patch('openstack_dashboard.api.heat.stack_get',
                   return_value=stack):
            ret_val = oc.is_deployed
            self.assertFalse(ret_val)

    def test_overcloud_all_resources(self):
        oc = api.Overcloud(self.tuskarclient_overclouds.first(), request=None)

        # FIXME(lsmola) the stack call should not be tested in this unit test
        # anybody has idea how to do it?
        stack = self.heatclient_stacks.first()
        resources = self.heatclient_resources.list()
        nodes = self.ironicclient_nodes.list()
        instances = []

        with patch('openstack_dashboard.api.heat.resources_list',
                   return_value=resources):
            with patch('openstack_dashboard.api.nova.server_list',
                       return_value=(instances, None)):
                with patch('novaclient.v1_1.contrib.baremetal.'
                           'BareMetalNodeManager.list',
                           return_value=nodes):
                    with patch('openstack_dashboard.api.heat.stack_get',
                               return_value=stack):
                        ret_val = oc.all_resources()

        for i in ret_val:
            self.assertIsInstance(i, api.Resource)
        self.assertEqual(4, len(ret_val))

    def test_overcloud_resources(self):
        oc = api.Overcloud(self.tuskarclient_overclouds.first(), request=None)
        role = api.OvercloudRole(self.tuskarclient_overcloud_roles.first())

        # FIXME(lsmola) only all_resources and image_name should be tested
        # here, anybody has idea how to do that?
        image = self.glanceclient_images.first()
        stack = self.heatclient_stacks.first()
        resources = self.heatclient_resources.list()
        instances = self.novaclient_servers.list()
        nodes = self.ironicclient_nodes.list()
        with patch('openstack_dashboard.api.heat.resources_list',
                   return_value=resources) as resource_list:
            with patch('openstack_dashboard.api.nova.server_list',
                       return_value=(instances, None)) as server_list:
                with patch('openstack_dashboard.api.glance.image_get',
                           return_value=image) as image_get:
                    with patch('novaclient.v1_1.contrib.baremetal.'
                               'BareMetalNodeManager.list',
                               return_value=nodes) as node_list:
                        with patch('openstack_dashboard.api.heat.stack_get',
                                   return_value=stack) as stack_get:
                            ret_val = oc.resources(role)
                            self.assertEqual(resource_list.call_count, 1)
                            self.assertEqual(server_list.call_count, 1)
                            # TODO(lsmola) isn't it better to call image_list?
                            # this will call image_get for every unique image
                            # used that should not be much (4 images should be
                            # there for start)
                            # FIXME(lsmola) testing caching here is bad,
                            # because it gets cached for the whole tests run
                            self.assertEqual(image_get.call_count, 1)
                            # FIXME(lsmola) optimize this, it's enough to call
                            # node_list once
                            self.assertEqual(node_list.call_count, 1)
                            self.assertEqual(stack_get.call_count, 1)

        for i in ret_val:
            self.assertIsInstance(i, api.Resource)
        self.assertEqual(4, len(ret_val))

    def test_overcloud_dasboard_url_from_params(self):
        oc = api.Overcloud(self.tuskarclient_overclouds.first(), request=None)
        stack = self.heatclient_stacks.first()
        with contextlib.nested(
            patch('openstack_dashboard.api.heat.stack_get',
                  return_value=stack),
        ):
            ret_val = oc.dashboard_url

            self.assertEqual(ret_val, 'http://192.0.2.22')

    def test_overcloud_dasboard_url_from_control_node(self):
        resources = [mock.Mock(**{
            'node': mock.Mock(**{
                'driver_info': {'ip_address': '192.0.2.25'}})
        })]

        with contextlib.nested(
            patch('tuskar_ui.api.Overcloud.stack',
                  mock.Mock(**{
                      'spec_set': ['parameters'],
                      'parameters': {'NeutronPublicInterfaceIP': ''}
                  })),
            patch('tuskar_ui.api.Overcloud.resources',
                  return_value=resources),
            patch('tuskar_ui.api.OvercloudRole', **{
                  'spec_set': ['list'],
                  'list.return_value': [mock.Mock(**{
                      'image_name': 'overcloud-control'})]
                  }),
        ):
            oc = api.Overcloud(self.tuskarclient_overclouds.first(),
                               request=object())
            ret_val = oc.dashboard_url

            self.assertEqual(ret_val, 'http://192.0.2.25')

    def test_node_create(self):
        node = api.Node(self.ironicclient_nodes.first())

        # FIXME(lsmola) this should be mocking client call no Node
        with patch('novaclient.v1_1.contrib.baremetal.'
                   'BareMetalNodeManager.create',
                   return_value=node):
            ret_val = api.Node.create(
                self.request,
                node.driver_info['ipmi_address'],
                node.properties['cpu'],
                node.properties['ram'],
                node.properties['local_disk'],
                ['aa:aa:aa:aa:aa:aa'],
                ipmi_username='admin',
                ipmi_password='password')

        self.assertIsInstance(ret_val, api.Node)

    def test_node_get(self):
        node = self.ironicclient_nodes.first()
        instance = self.novaclient_servers.first()

        with patch('openstack_dashboard.api.nova.server_get',
                   return_value=instance):
            with patch('novaclient.v1_1.contrib.baremetal.'
                       'BareMetalNodeManager.get',
                       return_value=node):
                ret_val = api.Node.get(self.request, node.uuid)

        self.assertIsInstance(ret_val, api.Node)
        self.assertIsInstance(ret_val.instance, servers.Server)

    def test_node_get_by_instance_uuid(self):
        instance = self.novaclient_servers.first()
        node = self.ironicclient_nodes.first()
        nodes = self.ironicclient_nodes.list()

        with patch('openstack_dashboard.api.nova.server_get',
                   return_value=instance):
            with patch('novaclient.v1_1.contrib.baremetal.'
                       'BareMetalNodeManager.list',
                       return_value=nodes):
                ret_val = api.Node.get_by_instance_uuid(self.request,
                                                        node.instance_uuid)

        self.assertIsInstance(ret_val, api.Node)
        self.assertIsInstance(ret_val.instance, servers.Server)

    def test_node_list(self):
        instances = self.novaclient_servers.list()
        nodes = self.ironicclient_nodes.list()

        with patch('openstack_dashboard.api.nova.server_list',
                   return_value=(instances, None)):
            with patch('novaclient.v1_1.contrib.baremetal.'
                       'BareMetalNodeManager.list',
                       return_value=nodes):
                ret_val = api.Node.list(self.request)

        for node in ret_val:
            self.assertIsInstance(node, api.Node)
        self.assertEqual(5, len(ret_val))

    def test_node_delete(self):
        node = self.ironicclient_nodes.first()
        with patch('novaclient.v1_1.contrib.baremetal.'
                   'BareMetalNodeManager.delete',
                   return_value=None):
            api.Node.delete(self.request, node.uuid)

    def test_node_instance(self):
        node = self.ironicclient_nodes.first()
        instance = self.novaclient_servers.first()

        with patch('openstack_dashboard.api.nova.server_get',
                   return_value=instance):
            ret_val = api.Node(node).instance
        self.assertIsInstance(ret_val, servers.Server)

    def test_node_image_name(self):
        node = self.ironicclient_nodes.first()
        instance = self.novaclient_servers.first()
        image = self.glanceclient_images.first()

        with patch('openstack_dashboard.api.nova.server_get',
                   return_value=instance):
            with patch('openstack_dashboard.api.glance.image_get',
                       return_value=image):
                ret_val = api.Node(node).image_name
        self.assertEqual(ret_val, 'overcloud-control')

    def test_node_overcloud_role(self):
        node = self.ironicclient_nodes.first()
        instance = self.novaclient_servers.first()
        image = self.glanceclient_images.first()
        roles = self.tuskarclient_overcloud_roles.list()

        with contextlib.nested(
                patch('openstack_dashboard.api.nova.server_get',
                      return_value=instance),
                patch('openstack_dashboard.api.glance.image_get',
                      return_value=image),
                patch('tuskarclient.v1.overcloud_roles.'
                      'OvercloudRoleManager.list',
                      return_value=roles)):
            ret_val = api.Node(node).overcloud_role
        self.assertEqual(ret_val.name, 'Controller')

    def test_node_addresses(self):
        node = self.ironicclient_nodes.first()

        ret_val = api.Node(node).addresses
        self.assertEqual(2, len(ret_val))

    def test_resource_get(self):
        stack = self.heatclient_stacks.first()
        overcloud = api.Overcloud(self.tuskarclient_overclouds.first(),
                                  request=None)
        resource = self.heatclient_resources.first()

        with patch('openstack_dashboard.api.heat.resource_get',
                   return_value=resource):
            with patch('openstack_dashboard.api.heat.stack_get',
                       return_value=stack):
                ret_val = api.Resource.get(None, overcloud,
                                           resource.resource_name)
        self.assertIsInstance(ret_val, api.Resource)

    def test_resource_node(self):
        resource = self.heatclient_resources.first()
        nodes = self.ironicclient_nodes.list()
        instance = self.novaclient_servers.first()

        with patch('openstack_dashboard.api.nova.server_get',
                   return_value=instance):
            with patch('novaclient.v1_1.contrib.baremetal.'
                       'BareMetalNodeManager.list',
                       return_value=nodes):
                ret_val = api.Resource(resource, request=None).node
        self.assertIsInstance(ret_val, api.Node)
        self.assertIsInstance(ret_val.instance, servers.Server)

    def test_overcloud_role_list(self):
        roles = self.tuskarclient_overcloud_roles.list()

        with patch('tuskarclient.v1.overcloud_roles.OvercloudRoleManager.list',
                   return_value=roles):
            ret_val = api.OvercloudRole.list(self.request)

        for r in ret_val:
            self.assertIsInstance(r, api.OvercloudRole)
        self.assertEqual(4, len(ret_val))

    def test_overcloud_role_get(self):
        role = self.tuskarclient_overcloud_roles.first()

        with patch('tuskarclient.v1.overcloud_roles.OvercloudRoleManager.get',
                   return_value=role):
            ret_val = api.OvercloudRole.get(self.request, role.id)

        self.assertIsInstance(ret_val, api.OvercloudRole)
