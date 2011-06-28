${' '.join(labels)}
% for line in data:
${' '.join(str(datum) for datum in line)}
% endfor
