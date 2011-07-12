<%namespace file="../rst.mako" name="rst"/>
<%def name="render_metadata(metadata)">
% for key, value in metadata.items():
% if key not in ('label', 'misc'):
${key}: ${value}
% endif
% endfor
% if 'misc' in metadata:
${metadata['misc']}
% endif
</%def>

<%rst:title level="${0}">FunkLoad_ trend report</%rst:title>

.. sectnum::    :depth: 2


% for key in sorted(comparable_keys):
<%rst:title level="${2}">${key}</%rst:title>
.. image:: ${image_paths[(key, 'apdex')]}
.. image:: ${image_paths[(key, 'per_second')]}
.. image:: ${image_paths[(key, 'average')]}
% endfor

<%rst:title>List of reports</%rst:title>
% for idx, (report, date, metadata) in enumerate(reports):
    * Bench **${idx+1}** ${date}: ${report} ${render_metadata(metadata)}
% endfor

.. _FunkLoad: http://funkload.nuxeo.org/
