# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
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
"""Classes that render statistics.

$Id$
"""
import json
from utils import render_template
from funkload.ReportStats import StatsAggregator, STATS_COLUMNS

# ------------------------------------------------------------
# ReST rendering
#

class RenderRst:
    """Render stats in ReST format."""
    # number of slowest requests to display
    slowest_items = 5

    def __init__(self, config, stats, monitor, monitorconfig, options):
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

    def append(self, text):
        """Append text to rst output."""
        self.rst.append(text)

    def createMonitorCharts(self):
        pass

    def renderHook(self):
        """Hook for post processing"""
        pass

    def __repr__(self):
        

        return render_template('report/rst.mako',
            cycles = self.cycles,
            stats_columns=STATS_COLUMNS,
            allstats=self.stats,
            aggregate_stats=self.aggr_stats,
            monitor_charts=self.createMonitorCharts(),
            config=self.config,
            date=self.date,
            apdex_t="%.1f" % self.options.apdex_t,
            image_paths=self.createResultCharts())



