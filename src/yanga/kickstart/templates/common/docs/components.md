# Components

{% for component in report_data.components %}

## {{ component.name }}


```{toctree}
:maxdepth: 1

{% for file in report_data.get_component_files_list(component.name) %}
{{ file }}
{% endfor %}

```


{% endfor %}
