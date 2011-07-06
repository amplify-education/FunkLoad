# (C) Copyright 2005-2011 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors:
#   Tom Lazar
#   Krzysztof A. Adamski
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
"""Html rendering

$Id$
"""
import os
from shutil import copyfile
from ReportRenderRst import RenderRst, rst_title


class RenderHtmlBase(RenderRst):
    """Render stats in html.

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    chart_size = (350, 250)
    big_chart_size = (640, 480)

    def __init__(self, config, stats, monitor, monitorconfig, options, css_file=None):
        RenderRst.__init__(self, config, stats, monitor, monitorconfig, options)
        self.css_file = css_file
        self.report_dir = self.css_path = self.rst_path = self.html_path = None

    def getChartSize(self, cvus):
        """Compute the right size lenght depending on the number of cvus."""
        size = list(self.chart_size)
        len_cvus = len(cvus)
        chart_size = self.chart_size
        big_chart_size = self.big_chart_size
        if ((len_cvus * 50) > chart_size[0]):
            if (len_cvus * 50 < big_chart_size):
                return ((len_cvus * 50), big_chart_size[1])
            return big_chart_size
        return chart_size

    def generateReportDirectory(self, output_dir):
        """Generate a directory name for a report."""
        config = self.config
        stamp = config['time'][:19].replace(':', '')
        stamp = stamp.replace('-', '')
        if config.get('label', None) is None:
            report_dir = os.path.join(output_dir, '%s-%s' % (
                config['id'], stamp))
        else:
            report_dir = os.path.join(output_dir, '%s-%s-%s' % (
                config['id'], stamp, config.get('label')))
        return report_dir

    def prepareReportDirectory(self):
        """Create a report directory."""
        if self.options.report_dir:
            report_dir = os.path.abspath(self.options.report_dir)
        else:
            # init output dir
            output_dir = os.path.abspath(self.options.output_dir)
            if not os.access(output_dir, os.W_OK):
                os.mkdir(output_dir, 0775)
            # init report dir
            report_dir = self.generateReportDirectory(output_dir)
        if not os.access(report_dir, os.W_OK):
            os.mkdir(report_dir, 0775)
        self.report_dir = report_dir

    def createRstFile(self):
        """Create the ReST file."""
        self.rst_path = os.path.join(self.report_dir, 'index.rst')
        with open(self.rst_path, 'w') as f:
            f.write(unicode(self).encode("utf-8"))

    def copyCss(self):
        """Copy the css to the report dir."""
        css_file = self.css_file
        if css_file is not None:
            css_dest_path = os.path.join(self.report_dir, css_file)
            copyfile(css_file, css_dest_path)
        else:
            # use the one in our package_data
            from pkg_resources import resource_string
            css_content = resource_string('funkload', 'data/funkload.css')
            css_dest_path = os.path.join(self.report_dir, 'funkload.css')
            f = open(css_dest_path, 'w')
            f.write(css_content)
            f.close()
        self.css_path = css_dest_path

    def copyXmlResult(self):
        """Make a copy of the xml result."""
        xml_src_path = self.options.xml_file
        xml_dest_path = os.path.join(self.report_dir, 'funkload.xml')
        copyfile(xml_src_path, xml_dest_path)

    def generateHtml(self):
        """Ask docutils to convert our rst file into html."""
        from docutils.core import publish_cmdline
        html_path = os.path.join(self.report_dir, 'index.html')
        cmdline = "-t --stylesheet-path=%s %s %s" % (self.css_path,
                                                     self.rst_path,
                                                     html_path)
        cmd_argv = cmdline.split(' ')
        publish_cmdline(writer_name='html', argv=cmd_argv)
        self.html_path = html_path


    def render(self):
        """Create the html report."""
        self.prepareReportDirectory()
        self.createRstFile()
        self.copyCss()
        try:
            self.generateHtml()
            pass
        except ImportError:
            print "WARNING docutils not found, no html output."
            return ''
        self.createCharts()
        self.copyXmlResult()
        return os.path.abspath(self.html_path)

    __call__ = render


    def createCharts(self):
        """Create all charts."""
        #self.createTestChart()
        #self.createPageChart()
        #self.createAllResponseChart()
        #for step_name in self.steps:
        #    self.createResponseChart(step_name)
        #for index, key in enumerate(self.pages):
        #    self.createResponseDescriptionChart(key, index)

    # monitoring charts
    def createMonitorCharts(self):
        """Create all monitored server charts."""
        if not self.monitor or not self.with_chart:
            return

        charts={}
        for host in self.monitor.keys():
            charts[host]=self.createMonitorChart(host)
        return charts

    def createResultCharts(self):
        """ Create all aggregate and breakout results charts """
        if not self.with_chart:
            return

        charts={}
        for group_name, grouped_stats in self.stats.items():
            for value, cycle_stats in grouped_stats.items():
                key = group_name, value
                charts[key] = self.createResultChart(key, cycle_stats)
        
        for group_name, aggregate_stats in self.aggr_stats.items():
            charts[group_name] = self.createResultChart(group_name, aggregate_stats)
        
        return charts
