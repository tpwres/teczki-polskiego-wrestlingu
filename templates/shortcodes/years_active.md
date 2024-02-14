{% set data = load_data(path="data/years-active.json") -%}
{% set_global years = data | get(key=page.title) -%}
{% for name in page.extra|get(key='career_aliases', default=[]) -%}
  {% set alias_years = data | get(key=name) -%}
  {% set_global years = years | concat(with=alias_years) -%}
{% endfor -%}
{% set years = years|sort -%}
{% if years -%}
  {% set min = years | first -%}
  {% set max = years | last -%}
  {% if min == max -%}
    {{ min }}
  {% else -%}
    {{min}}..{{max}}
  {% endif -%}
{% else -%}
  Unknown
{% endif -%}
