<%namespace file="gnuplot.mako" name="g"/>
set output "${image_path}"
set title "Successful Pages Per Second"
set ylabel "Pages Per Second"
set grid back
set terminal png size ${chart_size[0]},${chart_size[1]}

% if has_error:
${g.multiplot(2, 2, 1.25, 1.25)}
% else:
${g.multiplot(2, 2, 1.4)}
% endif

% if not use_xticlabels:
set xrange [0:${maxCVUs+1}]
set bmargin .5
set tmargin .5
% else:
set bmargin 1
set tmargin 1
set xrange [0.5:${datapoints + .5}]
% endif

set format x ""
unset title
unset xlabel
set lmargin 8
set rmargin 9.5
set key inside top

${g.nextchart()}

plot "${data_path}" u ${g.columns(column_names, 'CUs', 'PS')} w linespoints lw 2 lt 2 t "per second"

${g.nextchart()}

set autoscale y
set ylabel "Duration (s)"
set bars 5.0
set style fill solid .25
plot "${data_path}" u ${g.columns(column_names, 'CUs', 'MED', 'MED', 'P95', 'P90')} \
    t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, \
"" u ${g.columns(column_names, 'CUs', 'P10', 'MIN', 'MED', 'MED')} \
    w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, \
"" u ${g.columns(column_names, 'CUs', 'AVG')} t "avg" w lines lt 3 lw 2

set boxwidth .9
set style fill solid .7
set ylabel "Apdex ${apdex_t}"
set yrange [0:1]
set key outside top

${g.nextchart()}

plot "${data_path}" u ${g.columns(column_names, 'CUs', 'E')} w boxes lw 2 lt rgb "#99CDFF" t "E", \
"" u ${g.columns(column_names, 'CUs', 'G')} w boxes lw 2 lt rgb "#00FF01" t "G", \
"" u ${g.columns(column_names, 'CUs', 'F')} w boxes lw 2 lt rgb "#FFFF00" t "F", \
"" u ${g.columns(column_names, 'CUs', 'P')} w boxes lw 2 lt rgb "#FF7C81" t "P", \
"" u ${g.columns(column_names, 'CUs', 'U')} w boxes lw 2 lt rgb "#C0C0C0" t "U"

set key inside top

% if has_error:
${g.nextchart()}
set ylabel "% errors"
set yrange [0:100]
plot "${data_path}" u ${g.columns(column_names, 'CUs', 'ERROR', 'TOTAL', format='(${ERROR}*100/${TOTAL})')} w boxes lt 1 lw 2 t "% Errors"
% endif


