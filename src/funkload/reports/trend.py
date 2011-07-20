# (C) Copyright 2011 Nuxeo SAS <http://nuxeo.com>
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
"""Trend report rendering

The trend report uses metadata from a funkload.metadata file if present.

The format of the metadata file is the following:
label:short label to be displayed in the graph
anykey:anyvalue
a multi line description in ReST will be displayed in the listing parts
"""
import os
import hashlib
from shutil import copyfile
from funkload.utils import render_template
from funkload.reports.extraction import extract_report_data
from funkload.gnuplot import gnuplot, gnuplot_scriptpath, strictly_monotonic

def extract(report_dir, startswith):
    """Extract line form the ReST index file."""
    f = open(os.path.join(report_dir, "index.rst"))
    line = f.readline()
    while line:
        if line.startswith(startswith):
            f.close()
            return line[len(startswith):].strip()
        line = f.readline()
    f.close()
    return None


def extract_date(report_dir):
    """Extract the bench date form the ReST index file."""
    tag = "* Launched: "
    value = extract(report_dir, tag)
    if value is None:
        print "ERROR no date found in rst report %s" % report_dir
        return "NA"
    return value


def extract_max_cus(report_dir):
    """Extract the maximum concurrent users form the ReST index file."""
    tag = "* Cycles of concurrent users: "
    value = extract(report_dir, tag)
    if value is None:
        print "ERROR no max CUs found in rst report %s" % report_dir
        return "NA"
    return value.split(', ')[-1][:-1]


def extract_metadata(report_dir):
    """Extract the metadata from a funkload.metadata file."""
    ret = {}
    try:
        f = open(os.path.join(report_dir, "funkload.metadata"))
    except IOError:
        return ret
    lines = f.readlines()
    f.close()
    for line in lines:
        sep = None
        if line.count(':'):
            sep = ':'
        elif line.count('='):
            sep = '='
        else:
            key = 'misc'
            value = line.strip()
        if sep is not None:
            key, value = line.split(sep, 1)
            ret[key.strip()] = value.strip()
        elif value:
            v = ret.setdefault('misc', '')
            ret['misc'] = v + ' ' + value
    return ret


class TrendReport(object):
    """
    Build a trend report comparing a sequence of funkload benchmarks

    `args`:
        A list of directories containing the reports to compare
    """
    def __init__(self, args):
        # Swap windows path separator backslashes for forward slashes
        # Windows accepts '/' but some file formats like rest treat the
        # backslash specially.
        self.args = [os.path.abspath(arg).replace('\\', '/') for arg in args]
        self.reports_metadata = [extract_metadata(report) for report in self.args]
        self.reports_name = [os.path.basename(report) for report in self.args]
        self.reports_data = [extract_report_data(os.path.join(report, 'index.rst')) for report in self.args]
        
        self.comparable_keys = None
        for data in self.reports_data:
            if self.comparable_keys is None:
                self.comparable_keys = set(data.keys())
            else:
                self.comparable_keys = self.comparable_keys.intersection(set(data.keys()))

    def generate_report_dir_name(self):
        """Generate a directory name for a report."""
        return 'trend-report'

    def store_data_files(self, report_dir):
        """
        Store the data files required to generate this report in `report_dir`

        `report_dir`:
            The directory to create the report in
        """
        for idx, report in enumerate(self.args):
            copyfile(
                os.path.join(report, 'index.rst'),
                os.path.join(report_dir, 'report_{idx}.rst'.format(idx=idx))
            )

    def render(self, output_format, image_paths={}):
        """
        Create the report in the specified output format

        `output_format`:
            The output format of the report (currently, can be rst or org)

        `image_paths`: dict
            A dictionary mapping image keys to their paths on disk
        """
        reports = self.args
        reports_date = [extract_date(report) for report in reports]
        self.max_cus = extract_max_cus(reports[0])
        return render_template(
            '{output_format}/trend.mako'.format(output_format=output_format),
            reports=zip(self.reports_name, reports_date, self.reports_metadata),
            comparable_keys=self.comparable_keys,
            image_paths=image_paths,
        )

    def render_charts(self, report_dir):
        """Render stats."""
        images = {}
        for key in sorted(self.comparable_keys):
            per_second, response_times, apdex = self.create_trend_chart(key, report_dir)
            images[(key, 'per_second')] = per_second
            images[(key, 'average')] = response_times
            images[(key, 'apdex')] = response_times
        return images

    def create_trend_chart(self, key, report_dir):
        """
        Create a chart showing data trends for the specified key across all stored reports.

        Returns a tuple with of 3 image paths, relative to the report dir:
        (entries per second, average response time, apdex score)

        `key`:
            A section key that exists in self.reports_data, that specifies the data to trend
            over

        `report_dir`:
            The path to the output directory to write the data, gnuplot, and images to
        """
        output_name = 'trend_{hash}'.format(hash=hashlib.md5(str(key)).hexdigest())
        per_second_name = output_name + '.per_second.png'
        average_response_name = output_name + '.average.png'
        apdex_name = output_name + '.apdex.png'
        per_second_path = gnuplot_scriptpath(report_dir, per_second_name)
        average_response_path = gnuplot_scriptpath(report_dir, average_response_name)
        apdex_path = gnuplot_scriptpath(report_dir, apdex_name)
        gplot_path = str(os.path.join(report_dir, output_name + '.gplot'))
        data_path = gnuplot_scriptpath(report_dir, output_name + '.data')

        labels = ['CUs', 'PS', 'Apdex*', 'AVG']
        data = []

        cycles = [int(v) for v in self.reports_data[0][key]['CUs']]

        for report_idx, report_data in enumerate(self.reports_data):
            for idx in range(len(cycles)):
                values = [report_idx]
                for column_name in labels:
                    values.append(report_data[key][column_name][idx])
                data.append(values)
            data.append(None)

        with open(data_path, 'w') as data_file:
            data_file.write(render_template(
                'gnuplot/data.mako',
                labels=labels,
                data=data
            ))

        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template(
                'gnuplot/trend.mako',
                per_second_path=per_second_path,
                average_response_path=average_response_path,
                apdex_path=apdex_path,
                use_xticlabels=not strictly_monotonic(cycles),
                data_path=data_path,
                key=key,
                column_names=labels,
                reports_name=self.reports_name,
                labels=[metadata.get('label') for metadata in self.reports_metadata],
                max_cus=max(cycles),
            ))
        gnuplot(gplot_path)

        return (per_second_name, average_response_name, apdex_name)
