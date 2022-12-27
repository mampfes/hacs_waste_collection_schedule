<!--
HIDDEN COMMENT
To display a concise document, the FAQ shows a summary of the questions and allows answers to be expanded/collapsed.
This is implemented using the following markup:

  <details>
  <summary>QUESTION TEXT GOES HERE</summary>
  <p>

  ANSWER GOES HERE - USED STANDARD MARKDOWN
  </p>
  </details>

The empty line after the <p> is intentional and is required for the expand/collapse to function correctly.
-->


<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Frequently Asked Questions, or "How Do I ...?"

<details>
<summary>How do I format dates?</summary>
<p>

Use [strftime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) in `value_template` or `date_template`:

```yaml
# returns "20.03.2020"
value_template: '{{value.date.strftime("%d.%m.%Y")}}'
date_template: '{{value.date.strftime("%d.%m.%Y")}}'

# returns "03/20/2020"
value_template: '{{value.date.strftime("%m/%d/%Y")}}'
date_template: '{{value.date.strftime("%m/%d/%Y")}}'

# returns "Fri, 03/20/2020"
value_template: '{{value.date.strftime("%a, %m/%d/%Y")}}'
date_template: '{{value.date.strftime("%a, %m/%d/%Y")}}'
```
</p>
</details>

<details>
<summary>How do I show the number of days to the next collection?</summary>
<p>

Set `value_template` within the sensor configuration:

```yaml
value_template: 'in {{value.daysTo}} days'
```
</p>
</details>

<details>
<summary>How do I show Today / Tomorrow instead of in 0 / 1 days?</summary>
<p>

Set `value_template` within the sensor configuration:

```yaml
# returns "Today" if value.daysTo == 0
# returns "Tomorrow" if value.daysTo == 1
# returns "in X days" if value.daysTo > 1
value_template: '{% if value.daysTo == 0 %}Today{% elif value.daysTo == 1 %}Tomorrow{% else %}in {{value.daysTo}} days{% endif %}'
```
</p>
</details>

<details>
<summary>How do I join waste types in a value_template?</summary>
<p>

Use the `join` filter:

```yaml
# returns "Garbage, Recycle"
value_template: '{{value.types|join(", ")}}'

# returns "Garbage+Recycle"
value_template: '{{value.types|join("+")}}'
```

Note: If you don't specify a `value_template`, waste types will be joined using the `separator` configuration variable.
</p>
</details>

<details>
<summary>How do I setup a sensor which shows only the days to the next collection?</summary>
<p>

Set `value_template` within the sensor configuration:

```yaml
value_template: '{{value.daysTo}}'
```
</p>
</details>

<details>
<summary>How do I setup a sensor which shows only the date of the next collection?</summary>
<p>

Set `value_template` within the sensor configuration:

```yaml
value_template: '{{value.date.strftime("%m/%d/%Y")}}'
```
</p>
</details>

<details>
<summary>How do I configure a sensor which shows only the waste type of the next collection?</summary>
<p>

Set `value_template` within the sensor configuration:

```yaml
value_template: '{{value.types|join(", ")}}'
```
</p>
</details>

<details>
<summary>How do I configure a sensor to show only collections of a specific waste type?
</summary>
<p>

Set `types` within the sensor configuration:

```yaml
sensor:
  - platform: waste_collection_schedule
    name: next_garbage_collection
    types:
      - Garbage

  - platform: waste_collection_schedule
    name: next_recycle_collection
    types:
      - Recycle
```

Note: If you have set an alias for a waste type, you must use the alias name.
</p>
</details>

<details>
<summary>How can I rename an waste type?</summary>
<p>

Set `alias` in the customize section of a source:

```yaml
waste_collection_schedule:
  sources:
    - name: NAME
      customize:
        - type: Very long garbage name
          alias: Garbage
        - type: Very long recycle name
          alias: Recycle
```
</p>
</details>

<details>
<summary>How can I hide a waste type I don't want to see?</summary>
<p>

Set `show` configuration variable to *false* in the customize section of a source:

```yaml
waste_collection_schedule:
  sources:
    - name: NAME
      customize:
        - type: Unwanted Waste Type
          show: false
```
</p>
</details>

<details>
<summary>How do I show a coloured Lovelace card depending on the due date?</summary>
<p>

You can use [Button Card](https://github.com/custom-cards/button-card) to create a coloured Lovelace cards:

![Button Card](/images/button-cards.png)

```yaml
# configuration.yaml
sensor:
  - platform: waste_collection_schedule
    name: MyButtonCardSensor
    value_template: '{{value.types|join(", ")}}|{{value.daysTo}}|{{value.date.strftime("%d.%m.%Y")}}|{{value.date.strftime("%a")}}'
```

```yaml
# button-card configuration
type: 'custom:button-card'
entity: sensor.mybuttoncardsensor
layout: icon_name_state2nd
show_label: true
label: |
  [[[
    var days_to = entity.state.split("|")[1]
    if (days_to == 0)
    { return "Today" }
    else if (days_to == 1)
    { return "Tomorrow" }
    else
    { return "in " + days_to + " days" }
  ]]]
show_name: true
name: |
  [[[
    return entity.state.split("|")[0]
  ]]]
state:
  - color: red
    operator: template
    value: '[[[ return entity.state.split("|")[1] == 0 ]]]'
  - color: orange
    operator: template
    value: '[[[ return entity.state.split("|")[1] == 1 ]]]'
  - value: default
```
</p>
</details>

<details>
<summary>Can I also use the Garbage Collection Card instead?</summary>
<p>

Yes, the [Garbage Collection Card](https://github.com/amaximus/garbage-collection-card) can also be used with *Waste Collection Schedule*:

```yaml
# configuration.yaml
sensor:
  - platform: waste_collection_schedule
    name: garbage_days
    details_format: appointment_types
    value_template: "{{ value.daysTo }}"
    types:
      - Garbage

  - platform: template
    sensors:
      garbage:
        value_template: >
          {% if states('sensor.garbage_days')|int > 2 %}
            2
          {% else %}
            {{ states('sensor.garbage_days')|int }}
          {% endif %}
        attribute_templates:
          next_date: "{{ state_attr('sensor.garbage_days', 'Garbage') }}"
          days: "{{ states('sensor.garbage_days')|int }}"
```

```yaml
# garbage-collection-card configuration
entity: sensor.garbage
type: 'custom:garbage-collection-card'
```
</p>
</details>

<details>
<summary>How can I sort waste type specific entities?</summary>
<p>

Prerequisites: You already have dedicated sensors per waste type and want to show the sensor with the next collection in a Lovelace card.

Add `add_days_to: True` to the configuration of all sensors you want to sort. This will add the attribute `daysTo` which can be used by e.g. [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) to sort entities by day of next collection.
</p>
</details>

