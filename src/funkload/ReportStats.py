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
"""Classes that collect statistics submitted by the result parser.

$Id: ReportStats.py 24737 2005-08-31 09:00:16Z bdelbosc $
"""
from __future__ import division
from heapq import heappop, heappush, heapify
from collections import defaultdict

class ErrorStat(object):
    """Collect Error or Failure stats."""
    def __init__(self, result, code, traceback, headers={}, body=None):
        self._result = result
        try:
            self._code = int(code)
        except TypeError:
            self._code = None
        self._headers = tuple(headers.items()) if headers else ()
        self._body = body or None
        self._traceback = traceback

    @property
    def result(self):
        return self._result

    @property
    def code(self):
        return self._code

    @property
    def headers(self):
        return dict(self._headers)

    @property
    def body(self):
        return self._body

    @property
    def traceback(self):
        return self._traceback

    @property
    def as_tuple(self):
        return (self.result, self.code, self._headers, self.body, self.traceback)

    def __hash__(self):
        return hash(self.as_tuple)

    def __eq__(self, other):
        return self.as_tuple == other.as_tuple

    def __cmp__(self, other):
        return cmp(self.as_tuple, other.as_tuple)


class MonitorStat:
    """Collect system monitor info."""
    def __init__(self, attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


class ApdexStat:
    def __init__(self, apdex_t):
        self.apdex_satisfied = 0
        self.apdex_tolerating = 0
        self.apdex_frustrating = 0
        self.apdex_satisfied_t = apdex_t
        self.apdex_tolerating_t = 4*apdex_t 
        self.apdex_t = apdex_t
        self.count = 0

    def add(self, duration):
        if duration < self.apdex_satisfied_t:
            self.apdex_satisfied += 1
        elif duration < self.apdex_tolerating_t:
            self.apdex_tolerating += 1
        else:
            self.apdex_frustrating += 1
        self.count += 1

    @property
    def raw_score(self):
        return self.apdex_satisfied + (self.apdex_tolerating/2)

    @property
    def score(self):
        if not self.count:
            return 0

        return self.raw_score / self.count


class StatsAccumulator(object):
    """
    Collect stats in as minimal a form as possible that will still allow the
    computation of various summary statistics
    """

    def __init__(self, duration, apdex_t=1.5):
        self.values = []
        self.min = float('inf')
        self.max = float('-inf')
        self.total = self.count = self.successes = self.errors = 0
        self._sorted = True
        self.apdex = ApdexStat(apdex_t)
        self.duration = duration
        self.per_second = {}
        self.error_details = defaultdict(int)
    
    def add_record(self, time, value, error=None):
        """
        Add an entry to this stats collection
        """
        self.values.append(value)
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.total += value
        self.count += 1
        second = int(time)
        self.per_second[second] = self.per_second.setdefault(second, 0) + 1
        self.apdex.add(value)

        if not error:
            self.successes += 1
        else:
            self.errors += 1
            self.error_details[error] += 1

        self._sorted = False

    def __len__(self):
        return len(self.values)

    def sort(self):
        if not self._sorted:
            self.values.sort()
            self._sorted = True

    @property
    def avg_per_second(self):
        return len(self)/self.duration

    @property
    def max_per_second(self):
        return max(self.per_second.values())

    @property
    def min_per_second(self):
        if self.avg_per_second < 1:
            return 0

        return min(self.per_secord.values())

    @property
    def ordered_values(self):
        self.sort()

        for v in self.values:
            yield v

    @property
    def apdex_score(self):
        return self.apdex.score

    @property
    def average(self):
        return self.total / len(self)

    def compute_percentiles(self, step):
        """
        Computes the percentiles for this accumulator. Once computed,
        the percentiles are set as attributes on this object.
        
        The attribute name will be "perc%d" % percentile.
        """
        if int(step) != step:
            raise ValueError("Can only compute integer percentiles")

        self.sort()

        entry_count = len(self)
        for perc in range(0, 100, step):
            index = int(perc / 100.0 * entry_count)
            value = self.values[index]
            setattr(self, "perc%d" % perc, value)

    def stats_list(self):
        self.compute_percentiles(5)
        apdex_score = self.apdex_score
        return [apdex_score, get_apdex_label(apdex_score),
                self.avg_per_second, self.max_per_second, len(self),
                self.successes, self.errors, self.min, self.average, self.max,
                self.perc10, self.perc50, self.perc90, self.perc95]


class StatsAggregator(object):
    """
    Aggregates the stats from multiple StatsAccumulators and StatsAggregators
    """

    def __init__(self, substats):
        self.substats = substats

    @property
    def max(self):
        return max(s.max for s in self.substats)
    
    @property
    def min(self):
        return min(s.min for s in self.substats)
    
    @property
    def errors(self):
        return sum(s.errors for s in self.substats)
    
    @property
    def successes(self):
        return sum(s.successes for s in self.substats)

    @property
    def total(self):
        return sum(s.total for s in self.substats)

    @property
    def average(self):
        return self.total / len(self)

    @property
    def avg_per_second(self):
        return len(self) / self.substats[0].duration

    @property
    def error_details(self):
        error_details = defaultdict(int)
        for stat in self.substats:
            for error, count in stat.error_details.items():
                error_details[error] = error_details[error] + count
        return error_details

    @property
    def per_second(self):
        per_second = defaultdict(int)
        for stat in self.substats:
            for sec, count in stat.per_second.items():
                per_second[sec] = per_second[sec] + count
        return per_second

    @property
    def max_per_second(self):
        return max(self.per_second.values())

    @property
    def min_per_second(self):
        if self.avg_per_second < 1:
            return 0

        return min(self.per_secord.values())

    @property
    def apdex_score(self):
        return sum(s.apdex.raw_score for s in self.substats) / len(self)

    @property
    def ordered_values(self):
        subvalues = [s.ordered_values for s in self.substats]
        next_values = [(next(s), s) for s in subvalues]
        heapify(next_values)
        
        while next_values:
            value, stream = heappop(next_values)
            yield value

            try:
                heappush(next_values, (next(stream), stream))
            except StopIteration:
                # Nothing else in this stream, so don't put it back on the stack
                pass
    
    def __len__(self):
        return sum(len(s) for s in self.substats)

    def compute_percentiles(self, step):
        """
        Computes the percentiles for this accumulator. Once computed,
        the percentiles are set as attributes on this object.
        
        The attribute name will be "perc%d" % percentile.
        """
        if int(step) != step:
            raise ValueError("Can only compute integer percentiles")

        percentile_names = defaultdict(list)
        entry_count = len(self)
        for perc in range(0, 100, step):
            index = int(perc / 100.0 * entry_count)
            percentile_names[index].append("perc%d" % perc)
        
        for index, value in enumerate(self.ordered_values):
            if index in percentile_names:
                for name in percentile_names[index]:
                    setattr(self, name, value)

    def stats_list(self):
        self.compute_percentiles(5)
        apdex_score = self.apdex_score
        return [apdex_score, get_apdex_label(apdex_score),
                self.avg_per_second, self.max_per_second, len(self),
                self.successes, self.errors, self.min, self.average, self.max,
                self.perc10, self.perc50, self.perc90, self.perc95]

STATS_COLUMNS = ['CUs', 'Apdex*', 'Rating', 'PS', 'maxPS', 'TOTAL', 'SUCCESS',
    'ERROR', 'MIN', 'AVG', 'MAX', 'P10', 'MED', 'P90', 'P95']


def get_apdex_label(score):
    if score < 0.5:
        return "UNACCEPTABLE"
    if score < 0.7:
        return "POOR"
    if score < 0.85:
        return "FAIR"
    if score < 0.94:
        return "Good"
    return "Excellent"



