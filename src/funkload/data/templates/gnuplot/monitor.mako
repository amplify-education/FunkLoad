set output "${image_path}"
set terminal png size ${width},${height*number_of_plots}
set grid back
set xdata time
set timefmt "%H:%M:%S"
set format x "%H:%M"
set multiplot layout ${number_of_plots}, 1
% for (title, ylabel, unit, descriptors) in plots:
set title "${title}"
set ylabel "${ylabel}\
% if unit:
[${unit}]\
% endif
"
plot "${data_path}"\
% for i, (column, title, format) in enumerate(descriptors):
% if i > 0:
, ""\
% endif
 u 1:${column} title "${title}" with ${format}\
% endfor
% endfor

