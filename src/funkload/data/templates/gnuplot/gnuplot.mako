<%def name="columns(column_names, xaxis, *column_list, **options)">\
<%
def index(col):
    return column_names.index(col) + 1

xcol = index(xaxis)
format = options.get('format')
if format is not None:
    col_map = dict((name, index(name)) for name in column_list)
    columns = format.format(**col_map)
else:
    columns = ':'.join(str(index(name)) for name in column_list)
%>\
% if use_xticlabels:
:${columns}:xticlabels(${xcol})\
% else:
${xcol}:${columns}\
% endif
</%def>

<%def name="multiplot(*ratios)">
<%
total = sum(ratios)
ratios = [float(r) / total for r in ratios]

shared['multichart_positions'] = ((r, sum(ratios[i+1:]), i == len(ratios) - 1)
    for (i, r) in enumerate(ratios))
%>
set multiplot
</%def>

<%def name="nextchart()">
<%
size, origin, lastchart = next(shared['multichart_positions'])
%>
set size 1, ${size}
set origin 0, ${origin}

% if lastchart:
set bmargin 3
set format x "% g"
set xlabel "Concurrent Users"
% endif
</%def>
