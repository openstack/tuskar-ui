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

from django.conf.urls import defaults

from tuskar_ui.infrastructure.overcloud import views


urlpatterns = defaults.patterns(
    '',
    defaults.url(r'^$', views.IndexView.as_view(), name='index'),
    defaults.url(r'^create/$', views.CreateView.as_view(),
                 name='create'),
    defaults.url(r'^(?P<overcloud_id>[^/]+)/$',
                 views.DetailView.as_view(), name='detail'),
    defaults.url(r'^(?P<overcloud_id>[^/]+)/resource_category/'
                 '(?P<category_id>[^/]+)$',
                 views.ResourceCategoryView.as_view(),
                 name='resource_category'),
)
