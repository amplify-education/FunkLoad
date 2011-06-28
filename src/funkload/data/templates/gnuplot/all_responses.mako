<%namespace file="gnuplot.mako" name="g"/>

set output "${image_path}"
set title "Requests Per Second"
set xlabel "Concurrent Users"
set ylabel "Requests Per Second"
set grid

% if not use_xticlabels:
set xrange [0:${maxCVUs+1}]
% endif

set terminal png size ${chart_size[0]},${chart_size[1]}

% if has_error:
set format x ""
set multiplot
unset title
unset xlabel
set size 1, 0.7
set origin 0, 0.3
set lmargin 5
set bmargin 0
% endif

plot "${data_path}" u <%g:columns>2</%g:columns> w linespoints lw 2 lt 2 t "RPS"

% if has_error:
set format x "% g"
set bmargin 3
set autoscale y
set style fill solid .25
set size 1.0, 0.3
set xlabel "Concurrent Users"
set ylabel "% errors"
set origin 0.0, 0.0
plot "${data_path}" u <%g:columns>3</%g:columns> w linespoints lt 1 lw 2 t "% Errors"
unset multiplot
set size 1.0, 1.0
% endif

set output "${image2_path}"
set title "Requests Response time"
set ylabel "Duration (s)"
set bars 5.0
set grid back
set style fill solid .25
plot "${data_path}" u <%g:columns>8:8:10:9</%g:columns> t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u <%g:columns>7:4:8:8</%g:columns> w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u <%g:columns>5</%g:columns> t "avg" w lines lt 3 lw 2
