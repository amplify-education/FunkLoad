${' '.join(labels)}
% for line in data:
% if line is None:

% else:
${' '.join(str(datum) for datum in line)}
% endif
% endfor
