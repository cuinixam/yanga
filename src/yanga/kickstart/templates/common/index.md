{% if report_data.has_component_scope %}

# Software Component Report - {{ report_data.component_name }}

**Variant:** {{ report_data.variant_name }}</br>
**Component:** {{ report_data.component_name }}</br>
**Platform:** {{ report_data.platform_name }}</br>
**Timestamp:** {{ env.timestamp }}

{{ report_data.create_component_myst_toc(report_data.component_name) }}

{% else %}

# Variant Report

**Variant:** {{ report_data.variant_name }}</br>
**Platform:** {{ report_data.platform_name }}</br>
**Timestamp:** {{ env.timestamp }}


```{toctree}
:maxdepth: 3
:caption: Contents

/docs/components
{% for file in report_data.get_variant_files_list() %}
{{ file }}
{% endfor %}

```

{% endif %}
