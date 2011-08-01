
<%def name="literal_block()">\
::

<%self:indented>${caller.body()}</%self:indented>
</%def>

<%def name="indented(amount=4)">\
${' '*amount + ('\n' + ' '*amount).join(capture(caller.body).split('\n'))}
</%def>

<%def name="title(level=1)">\
<%
    rst_level = ['=', '=', '-', '~', '^']
    char = rst_level[level]
    text = capture(caller.body).strip()
    length = len(str(text))
%>\
% if level == 0:
${char*length}
% endif
${text}
${char*length}
</%def>

