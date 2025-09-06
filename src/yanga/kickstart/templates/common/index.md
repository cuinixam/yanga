{% if report_config.has_component_scope %}

# Software Component Report - {{ report_config.component_name }}

**Variant:** {{ report_config.variant }}</br>
**Component:** {{ report_config.component_name }}</br>
**Platform:** {{ report_config.platform }}</br>
**Timestamp:** {{ env.timestamp }}

{{ report_config.create_component_myst_toc(report_config.component_name) }}

{% else %}

# Variant Report

**Variant:** {{ report_config.variant }}</br>
**Platform:** {{ report_config.platform }}</br>
**Timestamp:** {{ env.timestamp }}


## Components

{% for component in report_config.components %}

### {{ component.name }}

{{ report_config.create_component_myst_toc(component.name) }}

{% endfor %}


```{toctree}
:maxdepth: 1

{% for file in report_config.get_variant_files_list() %}
{{ file }}
{% endfor %}

```


{% endif %}
