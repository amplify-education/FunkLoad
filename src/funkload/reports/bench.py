# (C) Copyright 2009 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Kelvin Ward
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""Render chart using gnuplot >= 4.2

$Id$
"""

from funkload.ReportStats import StatsAggregator, STATS_COLUMNS
import json
import os
import hashlib
from datetime import datetime
from funkload.MonitorPlugins import MonitorPlugins
from funkload.MonitorPluginsDefault import MonitorCPU, MonitorMemFree, MonitorNetwork, MonitorCUs
from funkload.utils import render_template
from funkload.gnuplot import gnuplot, gnuplot_scriptpath, strictly_monotonic
from shutil import copyfile

class BenchReport(object):
    """
    A report concerning a single bench test
    """
    def __init__(self, config, stats, monitor, monitorconfig, options, css_file=None):
        self.config = config
        self.stats = stats
        self.monitor = monitor
        self.monitorconfig = monitorconfig
        self.options = options
        self.rst = []
        self.image_paths = {}

        self.cycles = json.loads(config['cycles'])

        self.aggr_stats = {}
        for aggr_key, aggr_stats in self.stats.items():

            for cycle in range(len(self.cycles)):
                self.aggr_stats.setdefault(aggr_key, {})[cycle] = StatsAggregator([
                    cycle_stats[cycle] for cycle_stats in aggr_stats.values() if cycle in cycle_stats
                ])

        if options.html:
            self.with_chart = True
        else:
            self.with_chart = False

        self.date = config['time'][:19].replace('T', ' ')
        self.css_file = css_file
        self.css_path = self.rst_path = self.html_path = None

    def generate_report_dir_name(self):
        """Generate a directory name for a report."""
        config = self.config
        stamp = config['time'][:19].replace(':', '')
        stamp = stamp.replace('-', '')
        if config.get('label', None) is None:
            report_dir_items = (config['id'], stamp)
        else:
            report_dir_items = (config['id'], stamp, config.get('label'))
        return '-'.join(report_dir_items)

    def store_data_files(self, report_dir):
        xml_dest_path = os.path.join(report_dir, 'funkload.xml')
        copyfile(self.options.xml_file, xml_dest_path)

    def render(self, output_format, image_paths={}):
        return render_template(
            '{output_format}/bench.mako'.format(output_format=output_format),
            cycles = self.cycles,
            stats_columns=STATS_COLUMNS,
            allstats=self.stats,
            aggregate_stats=self.aggr_stats,
            image_paths=image_paths,
            config=self.config,
            date=self.date,
            apdex_t="%.1f" % self.options.apdex_t,
            monitor_hosts=self.monitor,
        )

    def getMonitorConfig(self, host):
        """Return the host config or a default for backward compat"""
        if self.monitorconfig.has_key(host):
            return self.monitorconfig[host]
        return { 'MonitorCPU': MonitorCPU().getConfig(),
                 'MonitorMemFree': MonitorMemFree().getConfig(),
                 'MonitorNetwork': MonitorNetwork(None).getConfig(),
                 'MonitorCUs': MonitorCUs().getConfig() }

    def createResultChart(self, key, stats, report_dir):
        output_name = 'results_{hash}'.format(hash=hashlib.md5(str(key)).hexdigest())
        image_name = output_name + '.png'
        image_path = gnuplot_scriptpath(report_dir, image_name)
        gplot_path = str(os.path.join(report_dir, output_name + '.gplot'))
        data_path = gnuplot_scriptpath(report_dir, output_name + '.data')

        # data
        labels = STATS_COLUMNS + ["E", "G", "F", "P", "U"]
        data = []
        has_error = False
        apdex_t = self.options.apdex_t
        for cycle, cycle_stats in stats.items():
            values = [self.cycles[cycle]] + cycle_stats.stats_list()
            if cycle_stats.errors > 0:
                has_error = True
            score = cycle_stats.apdex_score

            apdex = ['0', '0', '0', '0', '0']
            if score < 0.5:
                apdex[4] = str(score)
            elif score < 0.7:
                apdex[3] = str(score)
            elif score < 0.85:
                apdex[2] = str(score)
            elif score < 0.94:
                apdex[1] = str(score)
            else:
                apdex[0] = str(score)
            data.append(values + apdex)
        if len(data) == 0:
            # No pages finished during a cycle
            return

        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=data
            ))
        
        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/result.mako',
                image_path=image_path,
                chart_size=[800, 800],
                maxCVUs=max(self.cycles),
                datapoints=len(self.cycles),
                use_xticlabels=not strictly_monotonic(self.cycles),
                data_path=data_path,
                has_error=has_error,
                apdex_t="%0.1f" % apdex_t,
                column_names=labels,
                shared={}
            ))
        gnuplot(gplot_path)

        return image_name

    def createMonitorChart(self, host, report_dir):
        """Create monitrored server charts."""
        stats = self.monitor[host]
        times = []
        cvus_list = []
        for stat in stats:
            test, cycle, cvus = stat.key.split(':')
            stat.cvus=cvus
            date = datetime.fromtimestamp(float(stat.time))
            times.append(date.strftime("%H:%M:%S"))
            #times.append(int(float(stat.time))) # - time_start))
            cvus_list.append(cvus)

        Plugins = MonitorPlugins()
        Plugins.registerPlugins()
        Plugins.configure(self.getMonitorConfig(host))

        charts=[]
        for plugin in Plugins.MONITORS.values():
            image_prefix = gnuplot_scriptpath(report_dir, '%s_%s' % (host, plugin.name))
            data_prefix = gnuplot_scriptpath(report_dir, '%s_%s' % (host, plugin.name))
            gplot_path = str(os.path.join(report_dir, '%s_%s.gplot' % (host, plugin.name)))
            r=plugin.gnuplot(times, host, image_prefix, data_prefix, gplot_path, [640, 540], stats)
            if r!=None:
                gnuplot(gplot_path)
                charts.extend(r)
        return charts

    def render_charts(self, report_dir):
        """
        Create all the charts for the report.

        Returns a dictionary mapping arbitrary image keys to their paths on disk
        """

        charts={}

        # Create all monitored server charts
        for host in self.monitor.keys():
            charts[host]=self.createMonitorChart(host, report_dir)

        # Create all aggregate and breakout results charts
        for group_name, grouped_stats in self.stats.items():
            for value, cycle_stats in grouped_stats.items():
                key = group_name, value
                charts[key] = self.createResultChart(key, cycle_stats, report_dir)
        
        for group_name, aggregate_stats in self.aggr_stats.items():
            charts[group_name] = self.createResultChart(group_name, aggregate_stats, report_dir)
        
        return charts
