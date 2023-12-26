{% set data = load_data(path="data/years-active.json") -%}
{% set years = data[page.title] | sort -%}
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
