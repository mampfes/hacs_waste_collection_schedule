# Iris Salten

Supported collection schedule for [Iris Salten](https://www.iris-salten.no/), covering Bodø and surrounding municipalities in Nordland, Norway.

The script uses the official Iris Salten API to dynamically look up your address and fetch the internal ID.

## Configuration via UI

1. Go to `Settings` -> `Devices & Services` -> `Add Integration`.
2. Search for `Waste Collection Schedule`.
3. Select `Iris Salten` from the list of providers.
4. Enter your street address and (optionally) your municipality.

## Configuration via `configuration.yaml`

### Configuration Variables

**adresse**
*(string) (required)*
Your street address exactly as it is written in the Iris Salten search field.

**kommune**
*(string) (optional)*
Your municipality (e.g., "Bodø kommune"). Providing this is recommended if your street name exists in multiple municipalities within the Iris Salten region.

### Basic Example

```yaml
waste_collection_schedule:
  sources:
    - name: iris_salten_no
      args:
        adresse: "Alsosgården 11"
        kommune: "Bodø kommune"
```

## Advanced Dashboard Setup

For a more advanced dashboard experience that splits multiple collections on the same day into separate rows and uses official Iris Salten icons, follow this setup.

### 1. Create the Sensor (via UI)

When adding or modifying the source in the Home Assistant UI, add a sensor with these settings:

* **Name:** `Tømmeplan` (This usually results in the entity ID `sensor.waste_collection_schedule_tommeplan`)
* **Details Format:** `Upcoming`
* **Count:** `15`
* **Value Template:** `{{ value.daysTo }}`

### 2. Frontend Card
<img width="507" height="449" alt="iris_salten" src="https://github.com/user-attachments/assets/d2422462-258b-4a40-a11b-7fc94071fea4" />

This setup uses the [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) and [template-entity-row](https://github.com/thomasloven/lovelace-template-entity-row) plugins from HACS. Add a "Manual" card to your dashboard and paste the following YAML:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Tømmeplan
  card_mod:
    style: |
      ha-card {
        background: linear-gradient(145deg, rgba(255,176,233,0.05) 0%, rgba(50,50,52,1) 100%);
        font-family: 'Montserrat', sans-serif;
      }
      .card-content {
        padding: 0px 15px 15px 0px;
      }
filter:
  template: >
    {%- set ns = namespace(rows=[]) -%}
    
    {# Fetch attributes from the sensor #}
    {%- set all_attrs = states.sensor.waste_collection_schedule_tommeplan.attributes -%}

    {# --- WASTE TYPES: Keywords, display names, and official Iris Salten icons --- #}
    {%- set avfallstyper = [
      {'keyword': 'Matavfall', 'name': 'Matavfall uten hageavfall', 'img': 'https://iris-salten.no/wp-content/themes/iris/assets/img/2110.png'},
      {'keyword': 'Papir', 'name': 'Papir og papp', 'img': 'https://iris-salten.no/wp-content/themes/iris/assets/img/2400.png'},
      {'keyword': 'Glass', 'name': 'Glass- og metallemballasje', 'img': 'https://iris-salten.no/wp-content/themes/iris/assets/img/2612.png'},
      {'keyword': 'Restavfall', 'name': 'Restavfall', 'img': 'https://iris-salten.no/wp-content/themes/iris/assets/img/9999.png'},
      {'keyword': 'Plast', 'name': 'Plastemballasje', 'img': 'https://iris-salten.no/wp-content/themes/iris/assets/img/3200.png'}
    ] -%}

    {%- set default_image = 'https://iris-salten.no/wp-content/themes/iris/assets/img/9999.png' -%}

    {# Iterate through all attributes #}
    {%- for dato, type_raw in all_attrs.items() -%}
      
      {# Check if the attribute key is a date (format: YYYY-MM-DD) #}
      {%- if dato | regex_match('\d{4}-\d{2}-\d{2}') -%}
        
        {# Convert the date to a timestamp for calculations #}
        {%- set date_ts = as_timestamp(dato ~ ' 00:00:00') | default(0) -%}
        {%- set days = ((date_ts - as_timestamp(today_at('00:00'))) / 86400) | int -%}
        
        {# Format the date nicely for display (e.g., 22.04.2026) #}
        {%- set display_date = date_ts | timestamp_custom('%d.%m.%Y') -%}

        {# --- FILTER: Only future dates and max 31 days --- #}
        {%- if days >= 0 and days <= 31 -%}
          
          {# NORWEGIAN UI STRINGS #}
          {%- if days == 0 -%} {%- set status_text = 'I dag!' -%}
          {%- elif days == 1 -%} {%- set status_text = 'I morgen' -%}
          {%- else -%} {%- set status_text = days ~ ' dager' -%}
          {%- endif -%}

          {# Use a namespace to store matches from the loop #}
          {%- set match_ns = namespace(types=[]) -%}
          {%- for t in avfallstyper -%}
            {%- if t.keyword in type_raw -%}
              {%- set match_ns.types = match_ns.types + [t] -%}
            {%- endif -%}
          {%- endfor -%}

          {# Fallback: If no known type is found, use the raw string #}
          {%- if match_ns.types | length == 0 -%}
            {%- set match_ns.types = [{'name': type_raw, 'img': default_image}] -%}
          {%- endif -%}

          {# Create a separate row for EACH waste type found on this date #}
          {%- for match in match_ns.types -%}
            {%- set row = {
              'type': 'custom:template-entity-row',
              'entity': 'sensor.waste_collection_schedule_tommeplan', 
              'name': match.name,
              'image': match.img,
              'state': status_text,
              'secondary': display_date,
              'sortering': date_ts,
              'card_mod': {
                'style': "
                  :host {
                    --mdc-icon-size: 34px;
                    padding-right: 0px;
                  }
                  state-badge {
                    background-color: transparent !important;
                    border-radius: 50% !important;
                    margin-left: 16px !important;
                    margin-right: 10px !important;
                    box-shadow: none !important;
                    overflow: hidden;
                  }
                "
              }
            } -%}
            
            {%- set ns.rows = ns.rows + [row] -%}
          {%- endfor -%}
          
        {%- endif -%}
      {%- endif -%}
    {%- endfor -%}

    {{ ns.rows | sort(attribute='sortering') | to_json }}
```
