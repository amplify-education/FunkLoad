<%namespace file="gnuplot.mako" name="g"/>
#  ${left_path} vs ${right_path} - ${key}

# COMMON SETTINGS
set grid  back
set xlabel "Concurrent Users"
set boxwidth 0.9 relative
set style fill solid 1

# RPS
set output "${per_second_path}"
set terminal png size 640,640
set multiplot title "Requests Per Second (Scalability)"
set title "Requests Per Second" offset 0, -2
set size 1, 0.67
set origin 0, 0.3
set ylabel ""
set format x ""
set xlabel ""
plot "${data_path}" u ${g.columns('L_CUs', 'L_PS', 'R_PS')} w filledcurves above t "B2<B1", \
     "" u ${g.columns('L_CUs', 'L_PS', 'R_PS')} w filledcurves below t "B2>B1", \
     "" u ${g.columns('L_CUs', 'L_PS')} w lines lw 2 t "B1", \
     "" u ${g.columns('L_CUs', 'R_PS')} w lines lw 2 t "B2"

# % RPS
set title "RPS B2/B1 %"  offset 0, -2
set size 1, 0.33
set origin 0, 0
set format y "% g%%"
set format x "% g"
set xlabel "Concurrent Users"

plot "${data_path}" u ${g.columns('L_CUs', 'L_PS', 'R_PS', format="(${R_PS}<${L_PS}?(((${R_PS}*100)/${L_PS}) - 100): 0)")} w boxes notitle, \
     "" u ${g.columns('L_CUs', 'L_PS', 'R_PS', format="(${R_PS}>=${L_PS}?(((${R_PS}*100)/${L_PS})-100): 0)")} w boxes notitle
unset multiplot


# RESPONSE TIMES
set output "${response_times_path}"
set terminal png size 640,640
set multiplot title "Request Response time (Velocity)"

# AVG
set title "Average"  offset 0, -2
set size 0.5, 0.67
set origin 0, 0.30
set ylabel ""
set format y "% gs"
set xlabel ""
set format x ""
plot "${data_path}" u ${g.columns('L_CUs', 'L_AVG', 'R_AVG')} w filledcurves below t "B1<B2", \
     "" u ${g.columns('L_CUs', 'L_AVG', 'R_AVG')} w filledcurves above t "B1>B2", \
     "" u ${g.columns('L_CUs', 'L_AVG')} w lines lw 2 t "B1", \
     "" u ${g.columns('L_CUs', 'R_AVG')} w lines lw 2 t "B2

# % AVG
set title "Average B1/B2 %"  offset 0, -2
set size 0.5, 0.31
set origin 0, 0
set format y "% g%%"
set format x "% g"
set xlabel "Concurrent Users"
plot "${data_path}" u ${g.columns('L_CUs', 'L_AVG', 'R_AVG', format="(${R_AVG}>${L_AVG}?(((${L_AVG}*100)/${R_AVG}) - 100): 0)")} w boxes notitle, \
"" u ${g.columns('L_CUs', 'L_AVG', 'R_AVG', format="(${R_AVG}<=${L_AVG}?(((${L_AVG}*100)/${R_AVG}) - 100): 0)")} w boxes notitle

# MEDIAN
set size 0.5, 0.31
set format y "% gs"
set xlabel ""
set format x ""

set title "Median"
set origin 0.5, 0.66
plot "${data_path}" u ${g.columns('L_CUs', 'L_MED', 'R_MED')} w filledcurves below notitle, \
"" u ${g.columns('L_CUs', 'L_MED', 'R_MED')} w filledcurves above notitle, \
"" u ${g.columns('L_CUs', 'L_MED')} w lines lw 2 notitle, \
"" u ${g.columns('L_CUs', 'R_MED')} w lines lw 2 notitle

# P90
set title "p90"
set origin 0.5, 0.33
plot "${data_path}" u ${g.columns('L_CUs', 'L_P90', 'R_P90')} w filledcurves below notitle, \
"" u ${g.columns('L_CUs', 'L_P90', 'R_P90')} w filledcurves above notitle, \
"" u ${g.columns('L_CUs', 'L_P90')} w lines lw 2 notitle, \
"" u ${g.columns('L_CUs', 'R_P90')} w lines lw 2 notitle

# MAX
set title "Max"
set origin 0.5, 0
set format x "% g"
set xlabel "Concurrent Users"
plot "${data_path}" u ${g.columns('L_CUs', 'L_MAX', 'R_MAX')} w filledcurves below notitle, \
"" u ${g.columns('L_CUs', 'L_MAX', 'R_MAX')} w filledcurves above notitle, \
"" u ${g.columns('L_CUs', 'L_MAX')} w lines lw 2 notitle, \
"" u ${g.columns('L_CUs', 'R_MAX')} w lines lw 2 notitle
unset multiplot

