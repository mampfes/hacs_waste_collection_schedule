# Neuenrade

Neuenrade is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.neuenrade.de> and find the waste collection calendar.
- Select your street and export the iCal file.
- Copy the URL and use it as the `url` parameter.
- The `year` parameter will be automatically updated.

## Examples

### Affelner Hammer

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.neuenrade.de/city_info/display/ical/m_calendar_ical.cfm?region_id=51&year=2025&city_id=313&street_id=186
        year_field: year
```
