# -*- coding: utf8 -*-
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

from django.core import urlresolvers
from django import http

from mox import IsA  # noqa

from tuskar_ui import api as tuskar
from tuskar_ui.test import helpers as test

INDEX_URL = urlresolvers.reverse('horizon:infrastructure:resources.unallocated'
                                 ':index')
RESOURCES_OVERVIEW_URL = urlresolvers.reverse('horizon:infrastructure:'
                                              'resources.overview:index')


class UnallocatedNodesTests(test.BaseAdminViewTests):
    def setUp(self):
        super(UnallocatedNodesTests, self).setUp()

    @test.create_stubs({
        tuskar.BaremetalNode: ('list',),
    })
    def test_index(self):
        unallocated_nodes = self.baremetal_nodes.list()

        tuskar.BaremetalNode.list(
            IsA(http.HttpRequest)).AndReturn(unallocated_nodes)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'infrastructure/resources.unallocated/index.html')

        self.assertItemsEqual(res.context['unallocated_nodes_table'].data,
                              unallocated_nodes)

    @test.create_stubs({
        tuskar.BaremetalNode: ('list',),
    })
    def test_index_nodes_list_exception(self):
        tuskar.BaremetalNode.list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.tuskar)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertRedirectsNoFollow(res, RESOURCES_OVERVIEW_URL)
