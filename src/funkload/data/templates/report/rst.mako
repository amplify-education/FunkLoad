<%
unique_errors = set()
for substats in allstats.values():
    for cycle_stats in substats.values():
        for cycle in cycle_stats.values():
            unique_errors.update(cycle.error_details.keys())
error_ids = dict((error, i) for (i, error) in enumerate(sorted(unique_errors)))
%>

<%def name="literal_block()">
::
${'    ' + '\n    '.join(capture(caller.body).split('\n'))}
</%def>

<%def name="title(level=1)">
<%
    rst_level = ['=', '=', '-', '~', '^']
    char = rst_level[level]
    text = capture(caller.body).strip()
    length = len(str(text))
%>
% if level == 0:
${char*length}
% endif
${text}
${char*length}
</%def>

<%def name="render_stats_table(column_names, stats)">
<%! import itertools %>
<% 
def format_value(value):
    if isinstance(value, float):
        return "%.3f" % value
    else:
        return str(value)

def format_row(row):
    return [format_value(v) for v in row]

stats = [[str(cycles[cycle])] + format_row(row.stats_list())
    for (cycle, row) in sorted(stats.items())]

columns = zip(*([column_names] + stats))
column_widths = [max(len(v) for v in column) for column in columns]
%>

<%def name="divider()">\
${' '.join('='*w for w in column_widths)}\
</%def>

${divider()}
% for column, width in zip(column_names, column_widths):
${column.center(width)} \
% endfor

${divider()}
% for row in stats:
% for value, width in zip(row, column_widths):
${value.center(width)} \
% endfor

% endfor
${divider()}
</%def>

<%def name="render_stats(title, image_path, stats, level=1)">
<%self:title level="${level}">${title}</%self:title>
% if image_path in image_paths:
.. image:: ${image_paths[image_path]}
% endif

${render_stats_table(stats_columns, stats)}

% if sum(s.errors for s in stats.values()) > 0:
<%self:title level="${level+1}">Errors</%self:title>
% for cycle, cycle_stats in stats.items():
% if cycle_stats.errors > 0:
<%self:title level="${level+2}">Cycle ${cycle}</%self:title>
% for error, count in sorted(cycle_stats.error_details.items()):
- error${error_ids[error]}_: ${count}
% endfor
% endif
% endfor
% endif

</%def>

<%def name="render_aggregate_stats(name, aggregated_stats, substats)">
${render_stats(name, name, aggregated_stats)}

% if len(substats) > 1:
% for substat, cycles_stats in sorted(substats.items()):
${render_stats_display(name, substat, cycles_stats)}
% endfor
% endif
</%def>

<%def name="render_stats_display(aggregate_name, stat_name, stats)">
${render_stats(stat_name, (aggregate_name, stat_name), stats, 2)}
</%def>

<%def name="error_details()">
% for index, error in enumerate(sorted(unique_errors)):
.. _error${index}:
<%self:title level="${2}">Error ${index}</%self:title>

% if error.code >= 0:
<%self:title level="${3}">Http Response</%self:title>
HTTP ${error.code}
% for name, value in sorted(error.headers):
${name}: value
% endfor
% if error.body:
${error.body}
% endif
% endif

% if error.traceback:
<%self:title level="${3}">Traceback</%self:title>
<%self:literal_block>
${error.traceback}
</%self:literal_block>
% endif

% endfor
</%def>

<%block name="header_display">
<%self:title level="${0}">Funkload_ bench report</%self:title>

:date: ${date}
:abstract:
        ${config['class_description']}
        Bench result of ``${config['class']}.${config['method']}``
        ${config['description']}

.. _FunkLoad: http://funkload.nuxeo.org/
.. sectnum:: :depth: 2
.. contents:: Table of contents
    :depth: 2
.. |APDEXT| replace:: \ :sub:`${apdex_t}`
</%block>

<%block name="config_display">
<%self:title>Bench configuration</%self:title>
* Launched: ${date}
% if config.get('node'):
* From: ${config['node']}
% endif
* Test: ``${config['module']}.py ${config['class']}.${config['method']}``
% if config.get('label'):
* Label: ${config['label']}
% endif
* Target server: ${config['server_url']}
* Cycles of concurrent users: ${config['cycles']}
* Cycle duration: ${config['duration']}s
* Sleeptime between request: from ${config['sleep_time_min']}s to ${config['sleep_time_max']}s
* Sleeptime between test case: ${config['sleep_time']}s
* Startup delay between thread: ${config['startup_delay']}s
* Apdex: |APDEXT|
* FunkLoad_ version: ${config['version']}

<% metadata = dict((key[5:], value) for (key, value) in config.items() if key.startswith("meta:")) %>
% if metadata:
Bench metadata:
% for key, value in metadata.items():
* ${key}: ${value}
% endfor
% endif
</%block>

<%block name="bench_content">
</%block>

% for aggregate, stats in sorted(allstats.items()):
${render_aggregate_stats(aggregate, aggregate_stats[aggregate], stats)}
% endfor

% if monitor_charts:
<%self:title>Monitored hosts</%self:title>
<%block name="monitors">
% for host, charts in monitor_charts.items():
<%self:title level="${2}">${host}: ${config.get(host, '')}</%self:title>
% for chart_title, chart_image in charts:
**${chart_title}**

.. image:: ${chart_image}

% endfor
% endfor
</%block>
% endif

<%self:title>Error Details</%self:title>
${error_details()}

<%block name="definitions">
<%self:title>Definitions</%self:title>
* CUs: Concurrent users or number of concurrent threads executing tests.
* Request: a single GET/POST/redirect/xmlrpc request.
* Page: a request with redirects and resource links (image, css, js) for an html page.
* STPS: Successful tests per second.
* SPPS: Successful pages per second.
* RPS: Requests per second, successful or not.
* maxSPPS: Maximum SPPS during the cycle.
* maxRPS: Maximum RPS during the cycle.
* MIN: Minimum response time for a page or request.
* AVG: Average response time for a page or request.
* MAX: Maximmum response time for a page or request.
* P10: 10th percentile, response time where 10 percent of pages or requests are delivered.
* MED: Median or 50th percentile, response time where half of pages or requests are delivered.
* P90: 90th percentile, response time where 90 percent of pages or requests are delivered.
* P95: 95th percentile, response time where 95 percent of pages or requests are delivered.
* Apdex T: Application Performance Index, 
  this is a numerical measure of user satisfaction, it is based
  on three zones of application responsiveness:

  - Satisfied: The user is fully productive. This represents the
    time value (T seconds) below which users are not impeded by
    application response time.

  - Tolerating: The user notices performance lagging within
    responses greater than T, but continues the process.

  - Frustrated: Performance with a response time greater than 4*T
    seconds is unacceptable, and users may abandon the process.

    By default T is set to 1.5s this means that response time between 0
    and 1.5s the user is fully productive, between 1.5 and 6s the
    responsivness is tolerating and above 6s the user is frustrated.

    The Apdex score converts many measurements into one number on a
    uniform scale of 0-to-1 (0 = no users satisfied, 1 = all users
    satisfied).

    Visit http://www.apdex.org/ for more information.

* Rating: To ease interpretation the Apdex
  score is also represented as a rating:

  - U for UNACCEPTABLE represented in gray for a score between 0 and 0.5 

  - P for POOR represented in red for a score between 0.5 and 0.7

  - F for FAIR represented in yellow for a score between 0.7 and 0.85

  - G for Good represented in green for a score between 0.85 and 0.94

  - E for Excellent represented in blue for a score between 0.94 and 1.''')

Report generated with FunkLoad_ ${config['version']}
, more information available on the
`FunkLoad site <http://funkload.nuxeo.org/#benching>`
</%block>
