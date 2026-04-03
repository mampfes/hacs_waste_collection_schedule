# City of Windsor

City of Windsor is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://opendata.citywindsor.ca/Tools/WasteCollectionCalendar> and find your collection zone/location code.
- Use the URL `https://opendata.citywindsor.ca/api/events/wasteCollection/ical/?location=YOUR_LOCATION` replacing `YOUR_LOCATION` with your zone code (e.g. `4A`).
- Use this URL as the `url` parameter.

## Examples

### Location 4A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://opendata.citywindsor.ca/api/events/wasteCollection/ical/?location=4A
```
