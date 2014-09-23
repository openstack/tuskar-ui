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

from django.conf import urls

from tuskar_ui.infrastructure.nodes import views


urlpatterns = urls.patterns(
    '',
    urls.url(r'^$', views.IndexView.as_view(), name='index'),
    urls.url(r'^register/$', views.RegisterView.as_view(),
             name='register'),
    urls.url(r'^auto-discover/$', views.AutoDiscoverView.as_view(),
             name='auto-discover'),
    urls.url(r'^auto-discover-csv/$', views.AutoDiscoverCSVView.as_view(),
             name='auto-discover-csv'),
    urls.url(r'^(?P<node_uuid>[^/]+)/$', views.DetailView.as_view(),
             name='detail'),
    urls.url(r'^(?P<node_uuid>[^/]+)/performance/$',
             views.PerformanceView.as_view(), name='performance'),
)
