<%namespace file="gnuplot.mako" name="g"/>

set output "${image_path}"
set title "Successful Pages Per Second"
set ylabel "Pages Per Second"
set grid back

% if not use_xticlabels:
set xrange [0:${maxCVUs+1}]
% endif

set terminal png size ${chart_size[0]},${chart_size[1]}
set format x ""
set multiplot
unset title
unset xlabel
set bmargin 0
set lmargin 8
set rmargin 9.5
set key inside top

% if has_error:
set size 1, 0.4
set origin 0, 0.6
% else:
set size 1, 0.6
set origin 0, 0.4
% endif

plot "${data_path}" u <%g:columns>2</%g:columns> w linespoints lw 2 lt 2 t "SPPS"

set boxwidth 0.8
set style fill solid .7
set ylabel "Apdex ${apdex_t}"
set yrange [0:1]
set key outside top

% if has_error:
set origin 0.0, 0.3
set size 1.0, 0.3
% else:
set size 1.0, 0.4
set bmargin 3
set format x "% g"
set xlabel "Concurrent Users"
set origin 0.0, 0.0
% endif

plot "${data_path}" u <%g:columns>12</%g:columns> w boxes lw 2 lt rgb "#99CDFF" t "E", \
"" u <%g:columns>13</%g:columns> w boxes lw 2 lt rgb "#00FF01" t "G", \
"" u <%g:columns>14</%g:columns> w boxes lw 2 lt rgb "#FFFF00" t "F", \
"" u <%g:columns>15</%g:columns> w boxes lw 2 lt rgb "#FF7C81" t "P", \
"" u <%g:columns>16</%g:columns> w boxes lw 2 lt rgb "#C0C0C0" t "U"

unset boxwidth
set key inside top

% if has_error:
set bmargin 3
set format x "% g"
set xlabel "Concurrent Users"
set origin 0.0, 0.0
set size 1.0, 0.3
set ylabel "% errors"
set yrange [0:100]
plot "${data_path}" u <%g:columns>3</%g:columns> w boxes lt 1 lw 2 t "% Errors"
% endif

unset yrange
set autoscale y
unset multiplot
set size 1.0, 1.0
unset rmargin
set output "${image2_path}"
set title "Pages Response time"
set ylabel "Duration (s)"
set bars 5.0
set style fill solid .25
plot "${data_path}" u <%g:columns>8:8:10:9</%g:columns> t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u <%g:columns>7:4:8:8</%g:columns> w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u <%g:columns>5</%g:columns> t "avg" w lines lt 3 lw 2

