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
<summary>How do I configure sensors which show the first, second, third collection?</summary>
<p>

Set `event_index` within the sensor configuration:

```yaml
waste_collection_schedule:
  sensors:
    - name: first_garbage_collection
      event_index: 0
      value_template: '{{value.types|join(", ")}} in {{ value.daysTo }} days'

    - name: second_garbage_collection
      event_index: 1
      value_template: '{{value.types|join(", ")}} in {{ value.daysTo }} days'

    - name: third_garbage_collection
      event_index: 2
      value_template: '{{value.types|join(", ")}} in {{ value.daysTo }} days'
```

</p>
</details>

<details>
<summary>How do I configure a sensor to show only collections of a specific waste type?
</summary>
<p>

Set `types` within the sensor configuration:

```yaml
waste_collection_schedule:
  sensors:
    - name: next_garbage_collection
      types:
        - Garbage

    - name: next_recycle_collection
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
<summary>How do I show the next collection in my own language on a Lovelace card?</summary>
<p>

The sensor state and attributes contain only raw values (waste types, number of days, ISO date, color), so the card decides the wording. With the GUI's default overview sensors (see [Default sensors](/doc/installation.md#default-sensors)) you can use [Button Card](https://github.com/custom-cards/button-card) without splitting a text:

```yaml
# button-card configuration
type: custom:button-card
entity: sensor.waste_collection_schedule_next_collection # adjust to your entity id
layout: icon_name_state2nd
show_name: true
show_label: true
name: "[[[ return entity.state; ]]]" # the waste types of the next collection
label: |
  [[[
    const d = entity.attributes.daysTo;
    // Replace the words to match your language, e.g. "Heute" / "Morgen" / `in ${d} Tagen`
    if (d == 0) return "Today";
    if (d == 1) return "Tomorrow";
    return `in ${d} days`;
  ]]]
styles:
  icon:
    - color: "[[[ return entity.attributes.color; ]]]"
```

The weekday in the language of your browser can be derived from the ISO date in the `date` attribute:

```yaml
label: |
  [[[
    return new Date(entity.attributes.date).toLocaleDateString(undefined, { weekday: "long" });
  ]]]
```

For automations use the numeric **Days until collection** sensor, e.g. a `numeric_state` trigger with `below: 2` fires when the value drops to 1, the day before the collection. Waste types of that day are in the `next_types` attribute of **Next collection**.

</p>
</details>

<details>
<summary>How do I use the waste color on a Tile card (with card-mod)?</summary>
<p>

Every sensor with an upcoming collection has a `color` attribute (`#RRGGBB`). The Home Assistant [Tile card](https://www.home-assistant.io/dashboards/tile/) can only use a fixed color, but with [card-mod](https://github.com/thomasloven/lovelace-card-mod) it can follow the attribute:

```yaml
type: tile
entity: sensor.waste_collection_schedule_next_collection # adjust to your entity id
name: Next collection
state_content:
  - state
  - daysTo
card_mod:
  style: |
    ha-card {
      --tile-color: {{ state_attr(config.entity, 'color') or 'var(--primary-color)' }};
    }
```

The tile then shows the waste types and the number of days, and its icon takes the color of the next collection. `daysTo` is shown as a plain number; for wording like "Today" or "Tomorrow" in your language use the Button Card example in the entry above.

The same works for the per-type sensors, use their entity id instead.

</p>
</details>

<details>
<summary>How do I show a coloured Lovelace card depending on the due date?</summary>
<p>

You can use [Button Card](https://github.com/custom-cards/button-card) to create a coloured Lovelace cards:

![Button Card](/images/button-cards.png)

```yaml
# configuration.yaml
waste_collection_schedule:
  sensors:
    - name: MyButtonCardSensor
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
<summary>How do I color a Lovelace card with the color of the waste type?</summary>
<p>

Every sensor has a `color` attribute (a hex code such as `#9E5E23`) while a collection is upcoming. It is the color of the waste type, or the color the source provides for it, or the one you set with `color` in the `customize` section (YAML only). If several types are collected on the same day, it is the color of the first one.

The Tile card itself cannot read an attribute for its `color` option. With [card-mod](https://github.com/thomasloven/lovelace-card-mod) you can set the tile color from the attribute:

```yaml
type: tile
entity: sensor.waste_collection_schedule_paper
card_mod:
  style: |
    ha-card {
      --tile-color: {{ state_attr('sensor.waste_collection_schedule_paper', 'color') }};
    }
```

The [Mushroom template card](https://github.com/piitaya/lovelace-mushroom) can also use the attribute directly:

```yaml
type: custom:mushroom-template-card
entity: sensor.waste_collection_schedule_paper
primary: "{{ state_attr(entity, 'friendly_name') }}"
icon_color: "{{ state_attr(entity, 'color') }}"
```

</p>
</details>

<details>
<summary>Can I also use the Garbage Collection Card instead?</summary>
<p>

Yes, the [Garbage Collection Card](https://github.com/amaximus/garbage-collection-card) can also be used with *Waste Collection Schedule*:

```yaml
# configuration.yaml
waste_collection_schedule:
  sensors:
    - name: garbage_days
      details_format: appointment_types
      value_template: "{{ value.daysTo }}"
      types:
        - Garbage

sensor:
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
