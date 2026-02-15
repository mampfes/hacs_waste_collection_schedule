# City of Moonee Valley

Support for schedules provided by [City of Moonee Valley](https://www.mvcc.vic.gov.au/residents/bins-rubbish-recycling/collection-days/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moonee_valley_vic_gov_au
      args:
        property_location: PROPERTY_LOCATION
```

### Configuration Variables

**property_location**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: moonee_valley_vic_gov_au
      args:
        property_location: 1 Buckley Street ESSENDON 3040
```

## How to get the source arguments

Visit the [City of Moonee Valley Bin Collection page](https://www.mvcc.vic.gov.au/residents/bins-rubbish-recycling/collection-days/) and search for your address. The argument should match the address format shown in the search results.

Just run through the next configuration via UI process and you shouldn't need to worry about any of this.


## Configuration via UI

How I set up my system, you do you!

### Step 1: Add the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"Waste Collection Schedule"**
3. Select **"City of Moonee Valley"** as the source
4. Enter your address (e.g., `1 Buckley Street ESSENDON`)

### Step 2: Configure Sensors

After adding the source, select **"Show Sensor Configurations"** to create sensors for each bin type.

#### Sensor 1 - General Waste

- **Name:** `General Waste` (creates `sensor.general_waste_collection`)
- **Details Format:** Generic
- **Type(s):** General Waste
- **Value Template Preset:** In .. days: `in {{value.daysTo}} days`

**Note:** Before clicking submit, select **"Add additional sensors"** to create the next sensor.

#### Sensor 2 - Recycling

- **Name:** `Recycling` (creates `sensor.recycling_collection`)
- **Details Format:** Generic
- **Type(s):** Recycling
- **Value Template Preset:** In .. days: `in {{value.daysTo}} days`

**Note:** Before clicking submit, select **"Add additional sensors"** to create the next sensor.

#### Sensor 3 - FOGO

- **Name:** `Organics` (creates `sensor.organics_collection`)
- **Details Format:** Generic
- **Type(s):** FOGO
- **Value Template Preset:** In .. days: `in {{value.daysTo}} days`

**Note:** This is the last sensor, so you can submit without selecting "Add additional sensors".

### Step 3: Add a Display Card

To display which bins are due this week, you can add a Markdown card to your Home Assistant dashboard:

1. Go to your **Dashboard** → Click the **three dots** (⋮) → **Edit Dashboard**
2. Click **+ Add Card** → Search for **"Markdown"**
3. In the card editor, switch to the **Code Editor** view (YAML mode)
4. Paste the following configuration:

```yaml
type: markdown
content: >
  ## 🗑️ Bins This Week

  {% set bins_info = {
    'general': {'sensor': 'sensor.general_waste_collection', 'name': 'General waste', 'emoji': '🔴'},
    'recycling': {'sensor': 'sensor.recycling_collection', 'name': 'Recycling', 'emoji': '🟡'},
    'fogo': {'sensor': 'sensor.organics_collection', 'name': 'Organics', 'emoji': '🟢'}
  } %}

  {% set ns = namespace(collections=[]) %} {% for bin_name, info in
  bins_info.items() %}
    {% set upcoming = state_attr(info.sensor, 'upcoming') %}
    {% if upcoming and upcoming | length > 0 %}
      {% set next_collection = upcoming[0] %}
      {% set collection_date = next_collection['date'] %}
      {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
      {% set day_name = as_timestamp(collection_date ~ ' 00:00:00') | timestamp_custom('%A') %}
      {% if days >= 0 and days <= 7 %}
        {% set ns.collections = ns.collections + [{
          'name': info.name,
          'emoji': info.emoji,
          'days': days,
          'date': collection_date,
          'day_name': day_name,
          'is_tomorrow': days == 1,
          'is_today': days == 0
        }] %}
      {% endif %}
    {% endif %}
  {% endfor %}

  {% set sorted_collections = ns.collections | sort(attribute='days') %} {% set
  ns2 = namespace(dates_seen='') %}

  {% for collection in sorted_collections %}
    {% if collection.date not in ns2.dates_seen %}
      {% set ns2.dates_seen = ns2.dates_seen + '|' + collection.date %}
      
      {% if collection.is_today %}
  ⚠️ **COLLECTION TODAY!**
      {% elif collection.is_tomorrow %}
  ⏰ **Put out tonight - Collection tomorrow ({{ collection.day_name }})!**
      {% else %}
  📅 **Collection in {{ collection.days }} days** ({{ collection.day_name }}, {{
  collection.date }})
      {% endif %}

      {% for bin in sorted_collections %}
        {% if bin.date == collection.date %}
  {{ bin.emoji }} {{ bin.name }}
        {% endif %}
      {% endfor %}

  ---
    {% endif %}
  {% endfor %}
```

5. Click **Save** to add the card to your dashboard

This card will display all bin collections scheduled for the upcoming week, with special alerts for collections today or tomorrow.


### Step 4: Set Up Notifications (Optional)

To receive reminders on your phone the night before bin collection day, create the following automation:

1. Go to **Settings** → **Automations & Scenes** → Click **+ Create Automation** → **Create new automation**
2. Click the **three dots** (⋮) in the top right corner → Select **Edit in YAML**
3. Delete any existing content and paste the following configuration:

```yaml
alias: Bin Collection Reminder - All Users
description: Notify all users at 8pm on night before bin collection day
triggers:
  - at: "20:00:00"
    trigger: time
conditions:
  - condition: or
    conditions:
      - condition: template
        value_template: >
          {% set upcoming = state_attr('sensor.general_waste_collection',
          'upcoming') %} {% if upcoming and upcoming | length > 0 %}
            {% set collection_date = upcoming[0]['date'] %}
            {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
            {{ days == 1 }}
          {% else %}
            false
          {% endif %}
      - condition: template
        value_template: >
          {% set upcoming = state_attr('sensor.recycling_collection',
          'upcoming') %} {% if upcoming and upcoming | length > 0 %}
            {% set collection_date = upcoming[0]['date'] %}
            {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
            {{ days == 1 }}
          {% else %}
            false
          {% endif %}
      - condition: template
        value_template: >
          {% set upcoming = state_attr('sensor.organics_collection', 'upcoming')
          %} {% if upcoming and upcoming | length > 0 %}
            {% set collection_date = upcoming[0]['date'] %}
            {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
            {{ days == 1 }}
          {% else %}
            false
          {% endif %}
actions:
  - data:
      title: 🗑️ Bin Night Reminder
      message: >
        {% set bins = [] %} {% set general_upcoming =
        state_attr('sensor.general_waste_collection', 'upcoming') %} {% if
        general_upcoming and general_upcoming | length > 0 %}
          {% set collection_date = general_upcoming[0]['date'] %}
          {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
          {% if days == 1 %}
            {% set bins = bins + ['🔴 General Waste (Red bin)'] %}
          {% endif %}
        {% endif %}

        {% set recycling_upcoming = state_attr('sensor.recycling_collection',
        'upcoming') %} {% if recycling_upcoming and recycling_upcoming | length
        > 0 %}
          {% set collection_date = recycling_upcoming[0]['date'] %}
          {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
          {% if days == 1 %}
            {% set bins = bins + ['🟡 Recycling (Yellow bin)'] %}
          {% endif %}
        {% endif %}

        {% set organics_upcoming = state_attr('sensor.organics_collection',
        'upcoming') %} {% if organics_upcoming and organics_upcoming | length >
        0 %}
          {% set collection_date = organics_upcoming[0]['date'] %}
          {% set days = ((as_timestamp(collection_date ~ ' 00:00:00') - now().timestamp()) / 86400) | round(0, 'ceil') | int %}
          {% if days == 1 %}
            {% set bins = bins + ['🟢 FOGO (Green bin)'] %}
          {% endif %}
        {% endif %}

        Don't forget to put out tonight: {{ bins | join(', ') }}
    action: notify.notify
```

### Step 5: Customize and Enjoy

Play with and alter until your heart is content. I finally have a proper reminder.
Cheers, Mark