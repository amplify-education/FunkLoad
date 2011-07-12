# ${' '.join(reports_name)}

# COMMON SETTINGS
set grid  back
set boxwidth 0.9 relative

# Apdex
set output "${apdex_path}"
set terminal png size 640,380
set border 895 front linetype -1 linewidth 1.000
set grid nopolar
set grid xtics nomxtics ytics nomytics noztics nomztics \
 nox2tics nomx2tics noy2tics nomy2tics nocbtics nomcbtics
set grid layerdefault  linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set style line 100  linetype 5 linewidth 0.10 pointtype 100 pointsize default
#set view map
unset surface
set style data pm3d
set style function pm3d
set ticslevel 0
set nomcbtics
set xrange [ * : * ] noreverse nowriteback
set yrange [ * : * ] noreverse nowriteback
set zrange [ * : * ] noreverse nowriteback
set cbrange [ * : * ] noreverse nowriteback
set lmargin 0
set pm3d at s scansforward
# set pm3d scansforward interpolate 0,1
set view map
set title "Apdex Trend"
set xlabel "Bench"
set ylabel "CUs"
% for idx, label in enumerate(labels):
set label "${label}" at ${idx}, ${max_cus + 2}, 1 rotate by 45 front
% endfor
splot "${data_path}" using 1:2:3 with linespoints
unset label
set view

set output "${per_second_path}"
set title "Pages per second Trend"
splot "${data_path}" using 1:2:4 with linespoints

set output "${average_response_path}"
set palette negative
set title "Average response time (s)"
splot "${data_path}" using 1:2:5 with linespoints
