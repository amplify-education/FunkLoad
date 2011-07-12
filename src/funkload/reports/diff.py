# (C) Copyright 2008 Nuxeo SAS <http://nuxeo.com>
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
"""Classes that render a differential report

$Id$
"""
import os
from docutils.core import publish_doctree
from funkload.utils import render_template
import hashlib
from funkload.gnuplot import gnuplot, gnuplot_scriptpath, strictly_monotonic

def extract_table(table):
    column_names = [elem for elem in table.traverse() if elem.tagname == 'thead'][0][0]
    # Extract all rows from the table except the header row
    rows = [elem for elem in table.traverse() if elem.tagname == 'row'][1:]

    columns = {}
    for idx, column in enumerate(column_names):
        columns[column.astext()] = [row[idx].astext() for row in rows]

    return columns


def index_by_CUs(table):
    CUs = [int(cu) for cu in table['CUs']]
    columns_by_cu = {}
    for name, values in table.items():
        columns_by_cu[name] = dict(zip(CUs, values))

    return columns_by_cu


def extract_report_data(report_path):
    with open(report_path) as report:
        doc = publish_doctree(''.join(report.readlines()))

    # All stats tables are marked with a comment before-hand with the table
    # title in it
    stats_table_tag = 'stats_table '
    stats_table_markers = [elem for elem in doc.traverse()
        if (elem.tagname == 'comment' and
            elem[0].astext().startswith(stats_table_tag))]

    stats_tables = [extract_table(m.next_node(siblings=True, descend=False))
        for m in stats_table_markers]

    return dict(zip(
        (e[0].astext()[len(stats_table_tag):] for e in stats_table_markers),
        stats_tables
    ))


def getReadableDiffReportName(a, b):
    """Return a readeable diff report name using 2 reports"""
    a = os.path.basename(a)
    b = os.path.basename(b)
    if a == b:
        return "diff_" + a + "_vs_idem"
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            break
    for i in range(i, 0, -1):
        # try to keep numbers
        if a[i] not in "_-0123456789":
            i += 1
            break

    r = b[:i] + "_" + b[i:] + "_vs_" + a[i:]
    if r.startswith('test_'):
        r = r[5:]
    r = r.replace('-_', '_')
    r = r.replace('_-', '_')
    r = r.replace('__', '_')
    return "diff_" + r

def getRPath(a, b):
    """Return a relative path of b from a."""
    a_path = a.split('/')
    b_path = b.split('/')
    for i in range(min(len(a_path), len(b_path))):
        if a_path[i] != b_path[i]:
            break
    return '../' * len(a_path[i:]) + '/'.join(b_path[i:])


class DiffReport(object):
    def __init__(self, report_dir1, report_dir2, options, css_file=None):
        # Swap windows path separator backslashes for forward slashes
        # Windows accepts '/' but some file formats like rest treat the
        # backslash specially.
        self.report_dir1 = os.path.abspath(report_dir1).replace('\\', '/')
        self.report_dir2 = os.path.abspath(report_dir2).replace('\\', '/')
        self.options = options
        self.css_file = css_file
        self.header = None
        self.data1 = extract_report_data(os.path.join(self.report_dir1, 'index.rst'))
        self.data2 = extract_report_data(os.path.join(self.report_dir2, 'index.rst'))
        self.comparable_keys = set(self.data1.keys()) & set(self.data2.keys())
    
    def generate_report_dir_name(self):
        """Generate a directory name for a report."""
        return getReadableDiffReportName(self.report_dir1, self.report_dir2)

    def render(self, output_format, image_paths={}):
        return render_template(
            '{output_format}/diff.mako'.format(output_format=output_format),
            left_path=self.report_dir1,
            left_name=os.path.basename(self.report_dir1),
            right_path=self.report_dir2,
            right_name=os.path.basename(self.report_dir2),
            comparable_keys=self.comparable_keys,
            left_keys=set(self.data1.keys()),
            right_keys=set(self.data2.keys()),
            image_paths=image_paths,
        )

    def render_charts(self, report_dir):
        """Render stats."""
        images = {}
        for key in sorted(self.comparable_keys):
            per_second, response_times = self.create_diff_chart(key, report_dir)
            images[(key, 'per_second')] = per_second
            images[(key, 'response_times')] = response_times
        return images

    def create_diff_chart(self, key, report_dir):
        output_name = 'diff_{hash}'.format(hash=hashlib.md5(str(key)).hexdigest())
        per_second_name = output_name + '.per_second.png'
        response_times_name = output_name + '.response.png'
        per_second_path = gnuplot_scriptpath(report_dir, per_second_name)
        response_times_path = gnuplot_scriptpath(report_dir, response_times_name)
        gplot_path = str(os.path.join(report_dir, output_name + '.gplot'))
        data_path = gnuplot_scriptpath(report_dir, output_name + '.data')

        labels = []
        data = []

        left_data = self.data1[key]
        right_data = self.data2[key]

        columns = set(left_data.keys()) & set(right_data.keys())
        cycles = [int(v) for v in left_data['CUs']]

        for column_name in columns:
            labels.extend(['L_' + column_name, 'R_' + column_name])

        for idx in range(len(cycles)):
            values = []
            for column_name in columns:
                values.append(left_data[column_name][idx])
                values.append(right_data[column_name][idx])
            data.append(values)

        with open(data_path, 'w') as data_file:
            data_file.write(render_template(
                'gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template(
                'gnuplot/diff.mako',
                per_second_path=per_second_path,
                response_times_path=response_times_path,
                use_xticlabels=strictly_monotonic(cycles),
                left_path=self.report_dir1,
                right_path=self.report_dir2,
                data_path=data_path,
                key=key,
                column_names=labels,
            ))
        gnuplot(gplot_path)

        return (per_second_path, response_times_path)
