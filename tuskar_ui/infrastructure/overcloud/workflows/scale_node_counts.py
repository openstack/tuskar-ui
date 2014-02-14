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

from django.utils.translation import ugettext_lazy as _
import horizon.workflows

from tuskar_ui.infrastructure.overcloud.workflows import undeployed_overview


class Action(undeployed_overview.Action):
    class Meta:
        slug = 'scale_node_counts'
        name = _("Node Counts")

    def handle(self, request, context):
        return context


class Step(horizon.workflows.Step):
    action_class = Action
    contributes = ('node_counts',)
    template_name = 'infrastructure/overcloud/scale_node_counts.html'
