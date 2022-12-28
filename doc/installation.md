<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Installation

## Automated Installation Using HACS
![hacs_badge](https://img.shields.io/badge/HACS-Default-orange)
![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule)

The `Waste Collection Schedule` component can be installed via [HACS](https://hacs.xyz/). This allows you to be notified of any updates or new releases of the component.

After installing HACS:
1. Visit the HACS `Integrations` panel in Home Assistant.
2. Click `Explore & Download Repositories`.
3. Search for `Waste Collection Schedule`.
4. Click on the `Waste Collection Schedule` entry.
5. Click on `Download` to copy the relevant files to your `config/custom_components/` directory.
6. [Configure your waste collection source(s)](#configuring-waste-collection-schedules).
7. [Configure your waste collection sensor(s)](#configuring-waste-collection-schedules).
8. Restart Home Assistant.

## Manual Installation

1. Navigate to the [waste_collection_schedule](https://github.com/mampfes/hacs_waste_collection_schedule/tree/master/custom_components) directory.
2. Copy the `waste_collection_schedule` folder (including all files and subdirectories) to your Home Assistant `config/custom_components/` directory.
3. [Configure your waste collection source(s)](#configuring-waste-collection-schedules).
4. [Configure your waste collection sensor(s)](#configuring-waste-collection-schedules).
5. Restart Home Assistant.

# Configuring Waste Collection Schedules

To use Waste Collection Schedules, additional entries need to be made in your `configuration.yaml` file. The required entries are:

1. Configuring source(s)

   For each service provider, a source has to be added to the configuration. The source takes care of the arguments  required to get the correct information from the service provider's web page, e.g. district, city, street, house number, etc.

   If you have to fetch data from multiple service providers, you have to add multiple sources. You can also add the same service provider multiple times. This only makes sense if you use it with different arguments, e.g.  you are looking to display  waste collection schedules for multiple districts served by the same provider.

2. Configuring sensor(s)

   Sensors are used to visualize the retrieved information, e.g. waste type, next collection date, or number of days to next collection. The sensor state (which can be shown in a Lovelace/Mushroom cards) can be customized using templates. For example, you can display the collection type only, or the next collection date, or a combination of all available information.

   You can also add multiple sensors per source if you are going to display the information in separate entities. For example,  if you want each waste type to have its own entity, you can add one sensor per collection type.

## Configuring Source(s)

```yaml
waste_collection_schedule:
  sources:
    - name: SOURCE
      args:
        arg1: ARG1
        arg2: ARG2
        arg3: ARG3
      customize:
        - type: TYPE
          alias: ALIAS
          show: SHOW
          icon: ICON
          picture: PICTURE
          use_dedicated_calendar: USE_DEDICATED_CALENDAR
          dedicated_calendar_title: DEDICATED_CALENDAR_TITLE
      calendar_title: CALENDAR_TITLE
  fetch_time: FETCH_TIME
  random_fetch_time_offset: RANDOM_FETCH_TIME_OFFSET
  day_switch_time: DAY_SWITCH_TIME
  separator: SEPARATOR
```


| Parameter | Type | Requirement | Description |
|-----|-----|-----|-----|
| sources: | | required | Contains information for the service provider being used |
| name: | string | required | name of the service provider source to use. Should be the same as the source filename, but without the `.py` extension. See the [README](/README.md#supported-service-providers) for supported service providers |
| args: | various | required | source-specific arguments provided to service provider to unambiguously identify the collection schedule to return. Depending on the service provider, some arguments may be mandatory, and some may be optional. See individual sources for more details |
| customize: | | optional | Can be used to customise data retrieved from a source |
| type: | string | required | The identity of the waste type as returned from the source  |
| alias: | string | optional | A more readable, or user-friendly, name for the type of waste being collected. Default is `None` |
| show: | boolean | optional | Show (`True`) or hide (`False`) collections of this specific waste type. Default is `True` |
| icon: | string | optional | Icon to use for this specific waste type. Icons from the Home Assistant mdi icon set can be used. Default is `None`. |
| picture: | string | optional | string representation of the path to a picture used to represent this specific waste type. Default is `None` |
| use_dedicated_calendar: | boolean | optional | Creates a calendar dedicated to this specific waste type. Default is `False` |
| dedicated_calendar_title: | string | optional | A more readable, or user-friendly, name for this specific waste calendar object. If nothing is provided, the name returned by the source will be used |
| fetch_time: | time | optional | representation of the time of day in "HH:MM" that Home Assistant polls service provider for latest collection schedule. If no time is provided, the default of "01:00" is used |
| random_fetch_time_offset: | int | optional | randomly offsets the `fetch_time` by up to _int_ minutes. Can be used to distribute Home Assistant fetch commands over a longer time frame to avoid peak loads at service providers |
| day_switch_time: | time | optional | time of the day in "HH:MM" that Home Assistant dismisses the current entry and moves to the next entry. If no time if provided, the default of "10:00" is used. |
| separator: | string | optional | Used to join entries if the multiple values for a single day are returned by the source. If no value is entered, the default of ", " is used |

## Configuring source sensor(s)

Add the following lines to your `configuration.yaml` file:

```yaml
sensor:
  - platform: waste_collection_schedule
    source_index: SOURCE_INDEX
    name: NAME
    details_format: DETAILS_FORMAT
    count: COUNT
    leadtime: LEADTIME
    value_template: VALUE_TEMPLATE
    date_template: DATE_TEMPLATE
    add_days_to: ADD_DAYS_TO
    types:
      - Waste Type 1
      - Waste Type 2
```
| Parameter | Type | Requirement | Description |
|--|--|--|--|
| platform |  | required | waste_collection_schedule |
| source_index | int | optional | Used to assign a sensor to a specific source. Only needed if multiple sources are defined. The first source defined is source_index 0, the second source_index 1, etc. If no value is supplied, the default of 0 is used |
| name | string | required | The name Home Assistant used for this sensor |
| details_format | string | optional | Specifies the format used to display info in Home Assistant's _more info_ pop-up. Valid values are: `"upcoming"`, `"appointment_types"` and `"generic"`. If no value is supplied, the default of "upcoming" is used. See [options for details_format](#options-for-details_format-parameter) for more details |
| count | int | optional | Limits Home Assistant's _more info_ popup to displaying the next _int_ collections |
| leadtime | int | optional | Limits Home Assistant's _more info_ popup to only displaying collections happening within the next _leadtime_ days|
| value_template | string | optional | Uses Home Assistant templating to format the state information of an entity. See [template variables](#template-variables-for-value_template-and-date_template-parameters) for further details |
| date_template | string | optional | Uses Home Assistant templating to format the dates appearing within the _more info_ popup information of an entity. See [template variables](#template-variables-for-value_template-and-date_template-parameters) for further details |
| add_days_to | boolean | optional | Adds a `daysTo` attribute to the source entity state containing the number of days to  the next collection |
| types | list of strings | optional | Used to filter waste types. The sensor will only display collections matching these waste types |

## Options for _details_format_ parameter ##
Possible choices:
| upcoming | appointment_types | generic |
|--|--|--|
| shows a list of upcoming collections |shows a list of waste types and their next collection date | provides all attributes as generic Python data types. |
| ![Upcoming](/images/more-info-upcoming.png) | ![Waste Types](/images/more-info-appointment-types.png) | ![Generic](/images/more-info-generic.png) |

## Template variables for _value_template_ and _date_template_ parameters

The following variables can be used within `value_template` and `date_template`:

| Variable | Description | Type |Comments |
|--|--|--|--|
| `value.date` | Collection date | [datetime.date](https://docs.python.org/3/library/datetime.html#datetime.date) | Use [strftime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) to format the output |
| `value.daysTo` | Days to collection | int  | 0 = today, 1 = tomorrow, etc |
| `value.types`  | Waste types | list of strings | Use `join` filter to join types |

## HomeAssistant Service to manually update the source

If you want to manually update the source, you can call the service:

`waste_collection_schedule.fetch_data`

Normally the configuration parametet 'fetch_time' is used to do this periodically.

## Further help ##
For a full example, see [custom_components/waste_collection_schedule/waste_collection_schedule/source/example.py](/custom_components/waste_collection_schedule/waste_collection_schedule/source/example.py).

For other examples on how to configure source(s) and sensor(s), see the [FAQ](/doc/faq.md).
