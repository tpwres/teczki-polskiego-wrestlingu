{% if predicted %}
### Predicted card
{% elif incomplete %}
### Incomplete card
{% elif unofficial %}
### Unofficial card
{% else %}
### Card
{% endif %}
{% set card_header_used = true %}
