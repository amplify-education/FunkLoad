<%def name="labels(use_x_labels, cols)">\
% if use_x_labels:
${cols}:xticlabels(1)\
% else:
1:${cols}\
% endif
</%def>

set output "${image_path}"
set title "Successful Tests Per Second"
set terminal png size ${chart_size[0]}, ${chart_size[1]}
set xlabel "Concurrent Users"
set ylabel "Test/s"
set grid back

% if not use_xticlabels:
set xrange [0:${maxCVUs+1}]
% endif

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

plot "${data_path}" u ${labels(use_xticlabels, '2')} w linespoints lw 2 lt 2 t "STPS"

% if has_error:
set format x "%% g"
set bmargin 3
set autoscale y
set style fill solid .25
set size 1.0, 0.3
set ytics 20
set xlabel "Concurrent Users"
set ylabel "%% errors"
set origin 0.0, 0.0
set yrange [0:100]
plot "${data_path}" u ${labels(use_xticlabels, '2')} w linespoints lt 1 lw 2 t "%%%% Errors"
unset multiplot
% endif

