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
import copy

from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from openstack_dashboard.api import ceilometer
from openstack_dashboard.utils import metering

SETTINGS = {
    'settings': {
        'renderer': 'StaticAxes',
        'xMin': None,
        'xMax': None,
        'higlight_last_point': True,
        'auto_size': False,
        'auto_resize': False,
        'axes_x': False,
        'axes_y': True,
        'axes_y_label': False,
        'bar_chart_settings': {
            'orientation': 'vertical',
            'used_label_placement': 'left',
            'width': 30,
            'color_scale_domain': [0, 80, 80, 100],
            'color_scale_range': [
                '#0000FF',
                '#0000FF',
                '#FF0000',
                '#FF0000'
            ],
            'average_color_scale_domain': [0, 100],
            'average_color_scale_range': ['#0000FF', '#0000FF']
        }
    },
    'stats': {
        'average': None,
        'used': None,
        'tooltip_average': None,
    }
}

LABELS = {
    'hardware.cpu.load.1min': _("CPU load 1 min average"),
    'hardware.system_stats.cpu.util': _("CPU utilization"),
    'hardware.system_stats.io.outgoing.blocks': _("IO raw sent"),
    'hardware.system_stats.io.incoming.blocks': _("IO raw received"),
    'hardware.network.ip.outgoing.datagrams': _("IP out requests"),
    'hardware.network.ip.incoming.datagrams': _("IP in requests"),
    'hardware.memory.swap.util': _("Swap utilization"),
}


# TODO(lsmola) this should probably live in Horizon common
def query_data(request,
               date_from,
               date_to,
               group_by,
               meter,
               period=None,
               query=None,
               additional_query=None):

    if not period:
        period = metering.calc_period(date_from, date_to, 50)
    if additional_query is None:
        additional_query = []
    if date_from:
        additional_query += [{'field': 'timestamp',
                              'op': 'ge',
                              'value': date_from}]
    if date_to:
        additional_query += [{'field': 'timestamp',
                              'op': 'le',
                              'value': date_to}]

    # TODO(lsmola) replace this by logic implemented in I1 in bugs
    # 1226479 and 1226482, this is just a quick fix for RC1
    try:
        meter_list = [m for m in ceilometer.meter_list(request)
                      if m.name == meter]
        unit = meter_list[0].unit
    except Exception:
        raise
        unit = ""

    ceilometer_usage = ceilometer.CeilometerUsage(request)
    try:
        if group_by:
            resources = ceilometer_usage.resource_aggregates_with_statistics(
                query, [meter], period=period, stats_attr=None,
                additional_query=additional_query)
        else:
            resources = ceilometer_usage.resources_with_statistics(
                query, [meter], period=period, stats_attr=None,
                additional_query=additional_query)
    except Exception:
        resources = []
        exceptions.handle(request,
                          _('Unable to retrieve statistics.'))
    return resources, unit


def url_part(meter_name, barchart):
    d = {'meter': meter_name}
    if barchart:
        d['barchart'] = True
    return urlencode(d)


def get_meter_name(meter):
    return meter.replace('.', '_')


def get_meters(meters):
    return [(m, get_meter_name(m)) for m in meters]


def get_barchart_stats(series, unit):
    values = [point['y'] for point in series[0]['data']]
    average = sum(values) / len(values)
    used = values[-1]
    first_date = series[0]['data'][0]['x']
    last_date = series[0]['data'][-1]['x']
    tooltip_average = _('Average %(average)s %(unit)s<br> From: '
                        '%(first_date)s, to: %(last_date)s') % (
                            dict(average=average, unit=unit,
                                 first_date=first_date,
                                 last_date=last_date))
    return average, used, tooltip_average


def create_json_output(series, barchart, unit, date_from, date_to):
    start_datetime = end_datetime = ''
    if date_from:
        start_datetime = date_from.strftime("%Y-%m-%dT%H:%M:%S")
    if date_to:
        end_datetime = date_to.strftime("%Y-%m-%dT%H:%M:%S")

    settings = copy.deepcopy(SETTINGS)
    settings['settings']['xMin'] = start_datetime
    settings['settings']['xMax'] = end_datetime

    if series and barchart:
        average, used, tooltip_average = get_barchart_stats(series, unit)
        settings['settings']['yMin'] = 0
        settings['settings']['yMax'] = 100
        settings['stats']['average'] = average
        settings['stats']['used'] = used
        settings['stats']['tooltip_average'] = tooltip_average
    else:
        del settings['settings']['bar_chart_settings']
        del settings['stats']

    json_output = {'series': series}
    json_output = dict(json_output.items() + settings.items())
    return json_output


def get_nodes_stats(request, uuid, meter, date_options=None, date_from=None,
                    date_to=None, stats_attr=None, barchart=None,
                    group_by=None):

    unit = ''
    series = []

    if uuid:
        if group_by == "image_id":
            query = {}
            image_query = [{"field": "metadata.%s" % group_by,
                            "op": "eq",
                            "value": uuid}]
            query[uuid] = image_query
        else:
            query = [{'field': 'resource_id',
                      'op': 'eq',
                      'value': uuid}]
    else:
        # query will be aggregated across all resources
        group_by = "all"
        query = {'all': []}

    # Disk and Network I/O: data from 2 meters in one chart
    if meter == 'disk-io':
        meters = get_meters([
            'hardware.system_stats.io.outgoing.blocks',
            'hardware.system_stats.io.incoming.blocks'
        ])
    elif meter == 'network-io':
        meters = get_meters([
            'hardware.network.ip.outgoing.datagrams',
            'hardware.network.ip.incoming.datagrams'
        ])
    else:
        meters = get_meters([meter])

    date_from, date_to = metering.calc_date_args(
        date_from,
        date_to,
        date_options)

    for meter_id, meter_name in meters:
        label = unicode(LABELS.get(meter_id, meter_name))
        resources, unit = query_data(
            request=request,
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
            meter=meter_id,
            query=query)
        s = metering.series_for_meter(request, resources, group_by, meter_id,
                                      meter_name, stats_attr, unit, label)
        series += s

    series = metering.normalize_series_by_unit(series)

    json_output = create_json_output(
        series,
        barchart,
        unit,
        date_from,
        date_to)

    return json_output
