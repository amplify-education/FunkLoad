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
from ReportRenderRst import RenderRst


class RenderHtmlBase(RenderRst):
    """Render stats in html.

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    def __init__(self, config, stats, monitor, monitorconfig, options, css_file=None):
        RenderRst.__init__(self, config, stats, monitor, monitorconfig, options)
        self.css_file = css_file
        self.report_dir = self.css_path = self.rst_path = self.html_path = None

    def createRstFile(self):
        """Create the ReST file."""
        self.rst_path = os.path.join(self.report_dir, 'index.rst')
        with open(self.rst_path, 'w') as f:
            f.write(unicode(self).encode("utf-8"))

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
        self.copyXmlResult()
        return os.path.abspath(self.html_path)

    __call__ = render



