<%def name="columns()">\
% if use_xticlabels:
:${caller.body()}:xticlabels(1)\
% else:
1:${caller.body()}\
% endif
</%def>
