# (C) Copyright 2005-2011 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors:
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
"""Create an ReST or HTML report with charts from a FunkLoad bench xml result.

Producing html and png chart require python-docutils and gnuplot

$Id: ReportBuilder.py 24737 2005-08-31 09:00:16Z bdelbosc $
"""

USAGE = """%prog [options] xmlfile [xmlfile...]

or

  %prog --diff REPORT_PATH1 REPORT_PATH2

%prog analyze a FunkLoad bench xml result file and output a report.
If there are more than one file the xml results are merged.

See http://funkload.nuxeo.org/ for more information.

Examples
========
  %prog funkload.xml
                        ReST rendering into stdout.
  %prog --html -o /tmp funkload.xml
                        Build an HTML report in /tmp
  %prog --html node1.xml node2.xml node3.xml
                        Build an HTML report merging test results from 3 nodes.
  %prog --diff /path/to/report-reference /path/to/report-challenger
                        Build a differential report to compare 2 bench reports,
                        requires gnuplot.
  %prog --trend /path/to/report-dir1 /path/to/report-1 ... /path/to/report-n
                        Build a trend report using multiple reports.
  %prog -h
                        More options.
"""
try:
    import psyco
    psyco.full()
except ImportError:
    pass
import os
import xml.parsers.expat
from collections import defaultdict
from optparse import OptionParser, TitledHelpFormatter
from tempfile import NamedTemporaryFile

from ReportStats import StatsAccumulator, MonitorStat, ErrorStat
from MergeResultFiles import MergeResultFiles
from funkload.reports.bench import BenchReport
from funkload.reports.diff import DiffReport
from funkload.reports.trend import TrendReport
from utils import trace, get_version
from FunkLoadTestCase import RESPONSE_BY_STEP, RESPONSE_BY_DESCRIPTION, PAGE, TEST
from docutils.core import publish_cmdline

# ------------------------------------------------------------
# Xml parser
#
class FunkLoadXmlParser:
    """Parse a funkload xml results."""
    def __init__(self, apdex_t):
        """Init setup expat handlers."""
        self.apdex_t = apdex_t
        parser = xml.parsers.expat.ParserCreate()
        parser.buffer_text = True
        parser.CharacterDataHandler = self.handleCharacterData
        parser.StartElementHandler = self.handleStartElement
        parser.EndElementHandler = self.handleEndElement
        self.parser = parser
        self.current_element = [{'name': 'root'}]
        self.is_recording_cdata = False
        self.current_cdata = ''

        self.cycles = None
        self.cycle_duration = 0

        def nested_default_dict(constructor, depth=1):
            if depth <= 1:
                return defaultdict(constructor)
            else:
                def const():
                    return nested_default_dict(constructor, depth - 1)
                return defaultdict(const)

        def make_accum():
            return StatsAccumulator(float(self.cycle_duration), apdex_t)

        self.stats = nested_default_dict(make_accum, 3) # cycle stats
        self.monitor = {}                         # monitoring stats
        self.monitorconfig = {}                   # monitoring config
        self.config = {}

    def parse(self, xml_file):
        """Do the parsing."""
        try:
            self.parser.ParseFile(file(xml_file))
        except xml.parsers.expat.ExpatError, msg:
            if (self.current_element[-1]['name'] == 'funkload'
                and str(msg).startswith('no element found')):
                print "Missing </funkload> tag."
            else:
                print 'Error: invalid xml bench result file'
                if len(self.current_element) <= 1 or (
                    self.current_element[1]['name'] != 'funkload'):
                    print """Note that you can generate a report only for a
                    bench result done with fl-run-bench (and not on a test
                    resu1lt done with fl-run-test)."""
                else:
                    print """You may need to remove non ascii characters which
                    come from error pages caught during the bench test. iconv
                    or recode may help you."""
                print 'Xml parser element stack: %s' % [
                    x['name'] for x in self.current_element]
                raise

    def handleStartElement(self, name, attrs):
        """Called by expat parser on start element."""
        if name == 'funkload':
            self.config['version'] = attrs['version']
            self.config['time'] = attrs['time']
        elif name == 'config':
            self.config[attrs['key']] = attrs['value']
            if attrs['key'] == 'duration':
                self.cycle_duration = attrs['value']
        self.current_element.append({'name': name, 'attrs': attrs})

    # old element names: header, headers, body, testResult, response, monitor, monitorconfig

    def handleEndElement(self, name):
        """Processing element."""
        element = self.current_element.pop()
        attrs = element['attrs']
        cycle = int(attrs.get('cycle', -1))

        if name == 'aggregate':
            # Add this aggregation key to the list on the parent record
            self.current_element[-1]['attrs'].setdefault('aggregates', []).append(
                (element['attrs']['name'], "".join(element['contents'])))
        elif name in ('result', 'traceback', 'response_code', 'headers', 'body'):
            # set the result as an attribute of the parent record
            self.current_element[-1]['attrs'][name] = "".join(element['contents'])
        elif name == 'monitor':
            host = attrs.get('host')
            stats = self.monitor.setdefault(host, [])
            stats.append(MonitorStat(attrs))
        elif name == 'monitorconfig':
            host = attrs.get('host')
            config = self.monitorconfig.setdefault(host, {})
            config[attrs.get('key')]=attrs.get('value')
        # Handle all test results
        elif name in ('funkload', 'config'):
            # These get handled elsewhere
            pass
        else:
            time = float(attrs.get('time', -1))
            duration = float(attrs.get('duration', -1))
            result = attrs.get('result')
            successful = result == 'Successful'

            if not successful:
                error = ErrorStat(result=result,
                    code=attrs.get('code'), headers=attrs.get('headers'),
                    body=attrs.get('body'), traceback=attrs.get('traceback'))
            else:
                error = None

            def add_record(key, value):
                self.stats[key][value][cycle].add_record(
                    time,
                    duration,
                    error
                )

            # Handle new-style results files
            if name == 'record':
                for key, value in attrs.get('aggregates', []):
                    add_record(key, value)
            # Handle old-style results files
            elif name == 'testResult':
                add_record('Test', TEST.format(name=attrs['name']))
            elif name == 'response':
                if not attrs['url'].startswith('http'):
                    attrs['url'] = self.config['server_url'] + attrs['url']
                add_record('Response by step', RESPONSE_BY_STEP.format(**attrs))
                add_record('Response by description', RESPONSE_BY_DESCRIPTION.format(**attrs))
                if attrs['type'] in ('get', 'post', 'xmlrpc'):
                    add_record('Page', PAGE.format(**attrs))

    def handleCharacterData(self, data):
        self.current_element[-1].setdefault('contents', []).append(data)


def generate_html_report(report_dir, css_file=None):
    """
    Generate an html report from the index.rst file in report_dir
    """
    # Copy the css
    if css_file is not None:
        css_dest_path = os.path.join(report_dir, css_file)
        copyfile(css_file, css_dest_path)
    else:
        # use the one in our package_data
        from pkg_resources import resource_string
        css_content = resource_string('funkload', 'data/funkload.css')
        css_dest_path = os.path.join(report_dir, 'funkload.css')
        with open(css_dest_path, 'w') as css:
            css.write(css_content)

    # Build the html
    html_path = os.path.join(report_dir, 'index.html')
    rst_path = os.path.join(report_dir, 'index.rst')
    publish_cmdline(writer_name='html', argv=[
        '-t',
        '--stylesheet-path=' + css_dest_path,
        rst_path,
        html_path
    ])

    return html_path

def create_report_dir(options, report):
    if options.report_dir:
        report_dir = os.path.abspath(options.report_dir)
    else:
        # init output dir
        output_dir = os.path.abspath(options.output_dir)
        if not os.access(output_dir, os.W_OK):
            os.mkdir(output_dir, 0775)
        # init report dir
        report_dir = os.path.join(output_dir,
            report.generate_report_dir_name())
    if not os.access(report_dir, os.W_OK):
        os.mkdir(report_dir, 0775)
    return report_dir

# ------------------------------------------------------------
# main
#
def main():
    """ReportBuilder main."""
    parser = OptionParser(USAGE, formatter=TitledHelpFormatter(),
                          version="FunkLoad %s" % get_version())
    parser.add_option("-H", "--html", action="store_true", default=False,
                      dest="html", help="Produce an html report.")
    parser.add_option("--org", action="store_true", default=False,
                      dest="org", help="Org-mode report.")
    parser.add_option("-P", "--with-percentiles", action="store_true",
                      default=True, dest="with_percentiles",
                      help=("Include percentiles in tables, use 10%, 50% and"
                            " 90% for charts, default option."))
    parser.add_option("--no-percentiles", action="store_false",
                      dest="with_percentiles",
                      help=("No percentiles in tables display min, "
                            "avg and max in charts."))
    cur_path = os.path.abspath(os.path.curdir)
    parser.add_option("-d", "--diff", action="store_true",
                      default=False, dest="diffreport",
                      help=("Create differential report."))
    parser.add_option("-t", "--trend", action="store_true",
                      default=False, dest="trendreport",
                      help=("Build a trend reprot."))
    parser.add_option("-o", "--output-directory", type="string",
                      dest="output_dir",
                      help="Parent directory to store reports, the directory"
                      "name of the report will be generated automatically.",
                      default=cur_path)
    parser.add_option("-r", "--report-directory", type="string",
                      dest="report_dir",
                      help="Directory name to store the report.",
                      default=None)
    parser.add_option("-T", "--apdex-T", type="float",
                      dest="apdex_t",
                      help="Apdex T constant in second, default is set to 1.5s. "
                      "Visit http://www.apdex.org/ for more information.",
                      default=1.5)

    options, args = parser.parse_args()
    if options.diffreport:
        if len(args) != 2:
            parser.error("incorrect number of arguments")
        report = DiffReport(args[0], args[1], options)
    elif options.trendreport:
        if len(args) < 2:
            parser.error("incorrect number of arguments")
        report = TrendReport(args, options)
    else:
        if len(args) < 1:
            parser.error("incorrect number of arguments")
        if len(args) > 1:
            trace("Merging results files: ")
            f = NamedTemporaryFile(prefix='fl-mrg-', suffix='.xml')
            tmp_file = f.name
            f.close()
            MergeResultFiles(args, tmp_file)
            trace("Results merged in tmp file: %s\n" % os.path.abspath(tmp_file))
            args = [tmp_file]
        options.xml_file = args[0]
        xml_parser = FunkLoadXmlParser(options.apdex_t)
        xml_parser.parse(options.xml_file)
        
        report = BenchReport(xml_parser.config, xml_parser.stats,
                             xml_parser.monitor,
                             xml_parser.monitorconfig, options)

    if options.html:
        trace('Creating {type} ...\n'.format(type=report.__class__.__name__))
        report_dir = create_report_dir(options, report)
        image_paths = report.render_charts(report_dir)
        with open(os.path.join(report_dir, 'index.rst'), 'w') as index_rst:
            index_rst.write(report.render('rst', image_paths))
        html_path = generate_html_report(report_dir)
        trace('Wrote {output}.\n'.format(output=html_path))

    elif options.org:
        print unicode(report.render('org')).encode("utf-8")
    else:
        print unicode(report.render('rst')).encode("utf-8")


if __name__ == '__main__':
    main()
