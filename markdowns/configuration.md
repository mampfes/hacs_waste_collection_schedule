# Configuring Waste Collection Schedules

To use Waste Collection Schedules, additional entries need to be made in the `configuration.yaml` file. The two forms of entry are:

1. Configuring the source(s)

   For each service provider, a source has to be added to the configuration. The source takes care of the arguments which are required to get the correct information from the service provider's web page, e.g. district, city, street, house number, etc.

   If you have to fetch data from multiple service providers, you have to add multiple sources. You can also add the same service provider multiple times (which only makes sense if you use this with different arguments), e.g. if you are looking for displaying the waste collection schedules for multiple districts.

2. Configuring the sensor(s)

   A sensor is used to visualize the retrieved information, e.g. waste type, next collection date or number of days to next collection. The sensor state (which is shown in a Lovelace card) can be customized using templates. As an example, you may display the collection type only or the next collection date or a combination of all available information.

   You can also add multiple sensors per source if you are going to display the information in separate entities like the available collection types or the next collection date.

   If you are looking for displaying one entity per collection type, you just have to add one sensor per collection type.

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
| name: | string | required | name of the service provider source to use. Should be the same as the souce filename, but without the `.py` extension. See `!!!!` for supported service providers |
| args: | various | required | source-specific arguments provided to service provider to unambiguously identify the collection schedule to return. Depending on the service provider, some arguements may be mandatory, and some may be optional. See individual sources for more details |
| customize: | | optional | Can be used to customise data retreived from a source |
| type: | string | required | The identity of the waste type as returned from the source  |
| alias: | string | optional | A more readable, or user-friendly, name for the type of waste being collected. Default is `None` |
| show: | boolean | optional | Show (`True`) or hide (`False`) collections of this specific waste type. Default is `True` |
| icon: | string | optional | Icon to use for this specific waste type. Icons from the Home Assistant mdi icon set can be used. Default is `None`. |
| picture: | string | optional | string representaion of the path to a picture used to represent this specific waste type. Default is `None` |
| use_dedicated_calendar: | boolean | optional | Creates a calendar dedicated to this specific waste type. Default is `False` |
| dedicated_calendar_title: | string | optional | A more readable, or user-friendly, name for this specific waste calendar object. If nothing is provided, the name returned by the source will be used |
| fetch_time: | time | optional | representation of the time of day in "HH:MM" that Home Assistant polls service provider for latest collection schedule. If no time is provided, the default of "01:00" is used |
| random_fetch_time_offset: | int | optional | randomly offsets the `fetch_time` by up to _int_ minutes. Can be used to distribute Home Assistant fetch commands over a longer timeframe to avoid peak loads at service providers |
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
| details_format | string | optional | Specifies the format used to display info in Home Assistant's _more info_ pop-up. Valid values are: `"upcoming"`, `"appointment_types"` and `"generic"`. If no value is supplied, the default of "upcoming" is used. See `????` for more details |
| count | int | optional | Limits Home Assistant's _more info_ popup to displaying the next _int_ collections |
| leadtime | int | optional | Limits Home Assistant's _more info_ popup to only displaying collections happening within the next _leadtime_ days|
| value_template | string | optional | Uses Home Assistant templating to format the state information of an entity. See `???` for further details |
| date_template | string | optional | Uses Home Assistant templating to format the dates apperaing within the _more info_ popup information of an entity. See `???` for further details |
| add_days_to | boolean | optional | Adds a `daysTo` attribute to the source entity state containing the number of days to  the next collection |
| types | list of strings | optional | Used to filter waste types. The sensor will only display collections matching these waste types |

## Options for _details_format_ parameter ##
Possible choices:

- `upcoming` shows a list of upcoming collections.

  ![Upcoming](/doc/more-info-upcoming.png)

- `appointment_types` shows a list of waste types and their next collection date.

  ![Waste Types](/doc/more-info-appointment-types.png)

- `generic` provides all attributes as generic Python data types. This can be used by a specialized Lovelace card (`which doesn't exist so far????`).

  ![Generic](/doc/more-info-generic.png)


## Template variables for _value_template_ and _date_template_ parameters

The following variables can be used within `value_template` and `date_template`:

| Variable | Description | Type |Comments |
|--|--|--|--|
| `value.date` | Collection date | [datetime.date](https://docs.python.org/3/library/datetime.html#datetime.date) | Use [strftime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) to format the output |
| `value.daysTo` | Days to collection | int  | 0 = today, 1 = tomorrow, etc |
| `value.types`  | Waste types | list of strings | Use `join` filter to join types |

## Further help ##
For examples on how to configure source(s) and sensor(s), see the [FAQ](faq.md)