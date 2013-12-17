# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

import django.conf

from openstack_dashboard.api import base
from openstack_dashboard.test.test_data import utils
from tuskar_ui.cached_property import cached_property  # noqa
from tuskar_ui.test.test_data import tuskar_data
from tuskarclient.v1 import client as tuskar_client

LOG = logging.getLogger(__name__)
TUSKAR_ENDPOINT_URL = getattr(django.conf.settings, 'TUSKAR_ENDPOINT_URL')


# TODO(Tzu-Mainn Chen): remove test data when possible
def test_data():
    test_data = utils.TestDataContainer()
    tuskar_data.data(test_data)
    return test_data


# FIXME: request isn't used right in the tuskar client right now, but looking
# at other clients, it seems like it will be in the future
def tuskarclient(request):
    c = tuskar_client.Client(TUSKAR_ENDPOINT_URL)
    return c


class Stack(base.APIResourceWrapper):
    _attrs = ('id', 'stack_name', 'stack_status')

    @classmethod
    def create(cls, request, **kwargs):
        # Assumptions:
        #   * hard-coded stack name ('overcloud')
        #   * there is a Tuskar API/library that puts
        #     together the Heat template
        # Questions:
        #   * is the assumption correct, or does the UI have to
        #     do more heavy lifting?
        # Required:
        #   * Stack sizing information
        # Side Effects:
        #   * call out to Tuskar API/library, which deploys
        #     an 'overcloud' Stack using the sizing information
        # Return:
        #   * the created Stack object

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # stack = tuskarclient(request).stacks.create(
        #    'overcloud',
        #    kwargs['stack_sizing'])
        stack = test_data().heatclient_stacks.first

        return cls(stack)

    @classmethod
    def get(cls, request):
        # Assumptions:
        #   * hard-coded stack name ('overcloud')
        # Return:
        #   * the 'overcloud' Stack object

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # stack = heatclient(request).stacks.get('overcloud')
        stack = test_data().heatclient_stacks.first

        return cls(stack)

    @cached_property
    def resources(self):
        # Assumptions:
        #   * hard-coded stack name ('overcloud')
        # Return:
        #   * a list of Resources associated with the Stack

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # resources = heatclient(request).resources.list(self.id)
        resources = test_data().heatclient_resources.list

        return [Resource(r) for r in resources]

    @cached_property
    def nodes(self):
        # Assumptions:
        #   * hard-coded stack name ('overcloud')
        # Return:
        #   * a list of Nodes indirectly associated with the Stack

        return [resource.node for resource in self.resources]


class Node(base.APIResourceWrapper):
    # not entirely sure what's available from Ironic here
    _attrs = ('uuid', 'instance_uuid')

    @classmethod
    def create(cls, request, **kwargs):
        # Questions:
        #   * what parameters can we pass in?
        # Required:
        #   * ip_address, cpu, memory, local_disk, mac_address
        # Optional:
        #   * ipmi_user, ipmi_password
        # Side Effects:
        #   * call out to Ironic to registers a Node with the given
        #     parameters
        # Return:
        #   * the registered Node

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # node = ironicclient(request).nodes.create(
        #       kwargs['ip_address'],
        #       kwargs['cpu'])
        node = test_data().ironicclient_nodes.first

        return cls(node)

    @classmethod
    def get(cls, request, uuid):
        # Required:
        #   * uuid
        # Return:
        #   * the Node associated with the uuid

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # node = ironicclient(request).nodes.get(uuid)
        node = test_data().ironicclient_nodes.first

        return cls(node)

    @classmethod
    def list(cls, request, free=False):
        # Optional:
        #   * free
        # Return:
        #   * a list of Nodes registered in Ironic.
        #     if 'free' is True, only return those
        #     that are not associated with an Instance

        # TODO(Tzu-Mainn Chen): remove test data when possible
        # nodes = ironicclient(request).nodes.list()
        nodes = test_data().ironicclient_nodes.list()

        if free:
            return [cls(node) for node in nodes
                    if node.instance_uuid is None]
        else:
            return [cls(node) for node in nodes]

    @classmethod
    def delete(cls, request, uuid):
        # Required:
        #   * uuid
        # Side Effects:
        #   * remove the Node with the associated uuid from
        #     Ironic

        # TODO(Tzu-Mainn Chen): uncomment when possible
        # ironicclient(request).nodes.delete(uuid)
        return

    @cached_property
    def resource(self, stack):
        # Questions:
        #   * can we assume one resource per Node?
        # Required:
        #   * stack
        # Return:
        #   * return the node's associated Resource within the passed-in
        #     stack, if any

        return next(r for r in stack.resources
                    if r.physical_resource_id == self.instance_uuid)


class Resource(base.APIResourceWrapper):
    _attrs = ('resource_name', 'resource_type', 'resource_status',
              'physical_resource_id')

    @classmethod
    def get(cls, request, stack, resource_name):
        # Required:
        #   * stack, resource_name
        # Return:
        #   * the matching Resource in the stack

        # TODO(Tzu-Mainn Chen): uncomment when possible
        # resource = heatclient(request).resources.get(
        #     stack.id,
        #     resource_name)
        resources = test_data().heatclient_resources.list()
        resource = next(r for r in resources
                        if stack.id == r.stack_id
                        and resource_name == r.resource_name)

        return cls(resource)

    @cached_property
    def node(self):
        # Return:
        #   * return resource's associated Node

        return next(n for n in Node.list
                    if self.physical_resource_id == n.instance_uuid)

    @cached_property
    def resource_category(self):
        # Questions:
        #   * is a resource_type mapped directly to a ResourceCategory?
        #   * can we assume that the resource_type equals the category
        #     name?
        # Return:
        #   * the ResourceCategory matching this resource

        return ResourceCategory({'name': self.resource_type})


class ResourceCategory(base.APIResourceWrapper):
    _attrs = ('name')

    @cached_property
    def image(self):
        # Questions:
        #   * is the image name hardcoded somewhere?
        #   * when a user uploads an image, how do we enforce
        #     that it matches the image name?
        # Return:
        #   * the image name

        return "??????"

    @cached_property
    def resources(self, stack):
        # Questions:
        #   * can we assume that the resource_type equals the
        #     category name?
        # Required:
        #   * stack
        # Return:
        #   * the resources within the stack that match the
        #     resource category

        return (r for r in stack.resources if r.resource_type == self.name)
