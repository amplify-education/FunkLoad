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

import os
import sys
import re
import hashlib
from commands import getstatusoutput
from ReportRenderHtmlBase import RenderHtmlBase
from datetime import datetime
from MonitorPlugins import MonitorPlugins
from MonitorPluginsDefault import MonitorCPU, MonitorMemFree, MonitorNetwork, MonitorCUs
from utils import render_template
from ReportStats import STATS_COLUMNS

def gnuplot(script_path):
    """Execute a gnuplot script."""
    path = os.path.dirname(os.path.abspath(script_path))
    if sys.platform.lower().startswith('win'):
        # commands module doesn't work on win and gnuplot is named
        # wgnuplot
        ret = os.system('cd "' + path + '" && wgnuplot "' +
                        os.path.abspath(script_path) + '"')
        if ret != 0:
            raise RuntimeError("Failed to run wgnuplot cmd on " +
                               os.path.abspath(script_path))

    else:
        cmd = 'cd ' + path + '; gnuplot ' + os.path.abspath(script_path)
        ret, output = getstatusoutput(cmd)
        if ret != 0:
            raise RuntimeError("Failed to run gnuplot cmd: " + cmd +
                               "\n" + str(output))

def gnuplot_scriptpath(base, filename):
    """Return a file path string from the join of base and file name for use
    inside a gnuplot script.

    Backslashes (the win os separator) are replaced with forward
    slashes. This is done because gnuplot scripts interpret backslashes
    specially even in path elements.
    """
    return os.path.join(base, filename).replace("\\", "/")

class RenderHtmlGnuPlot(RenderHtmlBase):
    """Render stats in html using gnuplot

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    chart_size = (640, 540)
    ticpattern = re.compile('(\:\d+)\ ')

    def useXTicLabels(self):
        """Guess if we need to use labels for x axis or number."""
        cycles = self.cycles
        if len(cycles) <= 1:
            # single cycle
            return True
        if len(cycles) != len(set(cycles)):
            # duplicates cycles
            return True
        cycles = [int(i) for i in cycles]
        for i, v in enumerate(cycles[1:]):
            # unordered cycles
            if cycles[i] > v:
                return True
        return False

    def getMonitorConfig(self, host):
        """Return the host config or a default for backward compat"""
        if self.monitorconfig.has_key(host):
            return self.monitorconfig[host]
        return { 'MonitorCPU': MonitorCPU().getConfig(),
                 'MonitorMemFree': MonitorMemFree().getConfig(),
                 'MonitorNetwork': MonitorNetwork(None).getConfig(),
                 'MonitorCUs': MonitorCUs().getConfig() }

    def createMonitorChart(self, host):
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
            image_prefix = gnuplot_scriptpath(self.report_dir, '%s_%s' % (host, plugin.name))
            data_prefix = gnuplot_scriptpath(self.report_dir, '%s_%s' % (host, plugin.name))
            gplot_path = str(os.path.join(self.report_dir, '%s_%s.gplot' % (host, plugin.name)))
            r=plugin.gnuplot(times, host, image_prefix, data_prefix, gplot_path, [640, 540], stats)
            if r!=None:
                gnuplot(gplot_path)
                charts.extend(r)
        return charts
     
    def createResultChart(self, key, stats):
        output_name = 'results_{hash}'.format(hash=hashlib.md5(str(key)).hexdigest())
        image_name = output_name + '.png'
        image_path = gnuplot_scriptpath(self.report_dir, image_name)
        gplot_path = str(os.path.join(self.report_dir, output_name + '.gplot'))
        data_path = gnuplot_scriptpath(self.report_dir, output_name + '.data')

        # data
        labels = STATS_COLUMNS + ["E", "G", "F", "P", "U"]
        data = []
        has_error = False
        apdex_t = 0
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
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error,
                apdex_t="%0.1f" % apdex_t,
                column_names=labels,
                shared={}
            ))
        gnuplot(gplot_path)

        return image_name
