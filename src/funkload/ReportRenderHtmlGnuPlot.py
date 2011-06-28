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
from commands import getstatusoutput
from ReportRenderHtmlBase import RenderHtmlBase
from datetime import datetime
from MonitorPlugins import MonitorPlugins
from MonitorPluginsDefault import MonitorCPU, MonitorMemFree, MonitorNetwork, MonitorCUs
from utils import render_template

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

class FakeMonitorConfig:
    def __init__(self, name):
        self.name = name

class RenderHtmlGnuPlot(RenderHtmlBase):
    """Render stats in html using gnuplot

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    chart_size = (640, 540)
    #big_chart_size = (640, 480)
    ticpattern = re.compile('(\:\d+)\ ')

    def getChartSizeTmp(self, cvus):
        """Override for gnuplot format"""
        return str(self.chart_size[0]) + ',' + str(self.chart_size[1])

    def getXRange(self):
        """Return the max CVUs range."""
        return "[0:" + str(self.getMaxCVUs() + 1) + "]"

    def getMaxCVUs(self):
        """Return the max CVU."""
        maxCycle = self.config['cycles'].split(',')[-1]
        maxCycle = str(maxCycle[:-1].strip())
        if maxCycle.startswith("["):
            maxCycle = maxCycle[1:]
        return int(maxCycle)

    def useXTicLabels(self):
        """Guess if we need to use labels for x axis or number."""
        cycles = self.config['cycles'][1:-1].split(',')
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

    def fixXLabels(self, lines):
        """Fix gnuplot script if CUs are not ordered."""
        if not self.useXTicLabels():
            return lines
        # remove xrange line
        out = lines.replace('set xrange', '#set xrange')
        # rewrite plot using xticlabels
        out = out.replace(' 1:', ' :')
        out = self.ticpattern.sub(r'\1:xticlabels(1) ', out)
        return out

    def createTestChart(self):
        """Create the test chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'tests.png')
        gplot_path = str(os.path.join(self.report_dir, 'tests.gplot'))
        data_path  = gnuplot_scriptpath(self.report_dir, 'tests.data')
        stats = self.stats
        # data
        labels = ["CUs", "STPS", "ERROR"]
        cvus = []
        data = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle].has_key('test'):
                continue
            test = stats[cycle]['test']
            cvus.append(str(test.cvus))
            error = test.error_percent
            if error:
                has_error = True
            data.append((
                test.cvus,
                test.tps,
                error,
            ))
        if len(data) == 0:
            # No tests finished during the cycle
            return
        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        # script
        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/test.mako',
                image_path=image_path,
                chart_size=self.chart_size,
                maxCVUs=self.getMaxCVUs(),
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error
            ))
        gnuplot(gplot_path)

    def createPageChart(self):
        """Create the page chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'pages_spps.png')
        image2_path = gnuplot_scriptpath(self.report_dir, 'pages.png')
        gplot_path = str(os.path.join(self.report_dir, 'pages.gplot'))
        data_path = gnuplot_scriptpath(self.report_dir, 'pages.data')
        stats = self.stats
        # data
        labels = ["CUs", "SPPS", "ERROR", "MIN", "AVG", "MAX", "P10",
                "P50", "P90", "P95", "APDEX", "E", "G", "F", "P", "U"]
        data = []
        cvus = []
        has_error = False
        apdex_t = 0
        for cycle in self.cycles:
            if not stats[cycle].has_key('page'):
                continue
            page = stats[cycle]['page']
            cvus.append(str(page.cvus))
            error = page.error_percent
            if error:
                has_error = True
            apdex_t = page.apdex.apdex_t
            score = page.apdex_score

            values = [
                page.cvus,
                page.rps,
                error,
                page.min,
                page.avg,
                page.max,
                page.percentiles.perc10,
                page.percentiles.perc50,
                page.percentiles.perc90,
                page.percentiles.perc95,
                score,
            ]
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
            gplot_file.write(render_template('gnuplot/page.mako',
                image_path=image_path,
                image2_path=image2_path,
                chart_size=self.chart_size,
                maxCVUs=self.getMaxCVUs(),
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error,
                apdex_t="%0.1f" % apdex_t
            ))
        gnuplot(gplot_path)

    def createAllResponseChart(self):
        """Create global responses chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'requests_rps.png')
        image2_path = gnuplot_scriptpath(self.report_dir, 'requests.png')
        gplot_path = str(os.path.join(self.report_dir, 'requests.gplot'))
        data_path = gnuplot_scriptpath(self.report_dir, 'requests.data')
        stats = self.stats
        # data
        labels = ["CUs", "RPS", "ERROR", "MIN", "AVG", "MAX", "P10",
                "P50", "P90", "P95", "APDEX"]
        cvus = []
        data = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle].has_key('response'):
                continue
            resp = stats[cycle]['response']
            cvus.append(str(resp.cvus))
            error = resp.error_percent
            if error:
                has_error = True
            data.append((
                resp.cvus,
                resp.rps,
                error,
                resp.min,
                resp.avg,
                resp.max,
                resp.percentiles.perc10,
                resp.percentiles.perc50,
                resp.percentiles.perc90,
                resp.percentiles.perc95,
                resp.apdex_score,
            ))

        if len(data) == 0:
            # No result during a cycle
            return

        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/all_responses.mako',
                image_path=image_path,
                image2_path=image2_path,
                chart_size=self.chart_size,
                maxCVUs=self.getMaxCVUs(),
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error,
            ))
        gnuplot(gplot_path)

        return


    def createResponseChart(self, step):
        """Create responses chart."""
        image_path = gnuplot_scriptpath(self.report_dir,
                                        'request_%s.png' % step)
        gplot_path = str(os.path.join(self.report_dir,
                                      'request_%s.gplot' % step))
        data_path = gnuplot_scriptpath(self.report_dir,
                                       'request_%s.data' % step)
        stats = self.stats
        # data
        labels = ['CUs', 'STEP', 'ERROR', 'MIN', 'AVG', 'MAX', 'P10', 'P50', 'P90', 'P95', 'APDEX']
        cvus = []
        data = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle]['response_step'].has_key(step):
                continue
            resp = stats[cycle]['response_step'].get(step)
            cvus.append(str(resp.cvus))
            error = resp.error_percent
            if error:
                has_error = True
            data.append((
                resp.cvus,
                step,
                error,
                resp.min,
                resp.avg,
                resp.max,
                resp.percentiles.perc10,
                resp.percentiles.perc50,
                resp.percentiles.perc90,
                resp.percentiles.perc95,
                resp.apdex_score,
            ))
        if len(data) == 0:
            # No result during a cycle
            return
        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/response.mako',
                image_path=image_path,
                chart_size=self.chart_size,
                title="Request {step} Response time".format(step=step),
                maxCVUs=self.getMaxCVUs(),
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error
            ))
        gnuplot(gplot_path)

    def createResponseDescriptionChart(self, key, index):
        """Create responses chart."""
        key_path = key[0].replace('/', '_')
        image_path = gnuplot_scriptpath(self.report_dir,
                                        'request_%s_%s.png' % (key_path, index))
        gplot_path = str(os.path.join(self.report_dir,
                                      'request_%s_%s.gplot' % (key_path, index)))
        data_path = gnuplot_scriptpath(self.report_dir,
                                       'request_%s_%s.data' % (key_path, index))
        stats = self.stats
        # data
        labels = ['CUs', 'INDEX', 'ERROR', 'MIN', 'AVG', 'MAX', 'P10', 'P50', 'P90', 'P95', 'APDEX']
        cvus = []
        data = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle]['response_desc'].has_key(key):
                continue
            resp = stats[cycle]['response_desc'][key]
            cvus.append(str(resp.cvus))
            error = resp.error_percent
            if error:
                has_error = True
            data.append((
                resp.cvus,
                index,
                error,
                resp.min,
                resp.avg,
                resp.max,
                resp.percentiles.perc10,
                resp.percentiles.perc50,
                resp.percentiles.perc90,
                resp.percentiles.perc95,
                resp.apdex_score,
            ))
        if len(data) == 0:
            # No result during a cycle
            return
        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/response.mako',
                image_path=image_path,
                chart_size=self.chart_size,
                title="Request Response time",
                maxCVUs=self.getMaxCVUs(),
                use_xticlabels=self.useXTicLabels(),
                data_path=data_path,
                has_error=has_error
            ))
        gnuplot(gplot_path)

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
            r=plugin.gnuplot(times, host, image_prefix, data_prefix, gplot_path, self.chart_size, stats)
            if r!=None:
                gnuplot(gplot_path)
                charts.extend(r)
        return charts
