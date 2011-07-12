<%namespace file="../rst.mako" name="rst"/>

<%!
def path(incoming_path):
    return incoming_path.replace('\\', '/').replace('_', '\\_')
%>

<%rst:title level="${0}">FunkLoad_ differential report</%rst:title>

.. contents:: Table of contents
    :depth: 2
.. sectnum::    :depth: 2

<%rst:title level="${1}">${left_name} vs ${right_name}</%rst:title>
* Reference bench report **B1**: ${left_name} [#]_
* Challenger bench report **B2**: ${right_name} [#]_

% for key in sorted(comparable_keys):
<%rst:title level="${2}">${key}</%rst:title>
.. image:: ${image_paths[(key, 'per_second')]}
.. image:: ${image_paths[(key, 'response_times')]}
% endfor

.. [#] B1 path: ${left_path | path}
.. [#] B2 path: ${right_path | path}

.. _FunkLoad: http://funkload.nuxeo.org/

