# Strathfield Council

```yaml
waste_collection_schedule:
  sources:
    - name: strathfield_nsw_gov_au
      args:
        collection_day: "Monday"
```

Find your Monday-Friday collection day on your rates notice or the street guide linked from the [Residential Bin Collection page](https://www.strathfield.nsw.gov.au/Live/Waste/Residential-Bin-Collection).

`collection_day` keeps its existing name and accepts the collection weekday. The source reads the currently linked English PDF calendar. Green weeks mean general waste plus garden organics; yellow weeks mean general waste plus recycling.

Dates start today and stop at the published calendar's end. The source no longer emits historical dates or projects a fixed anchor two years ahead. If no current calendar is published, it raises an error. The PDF parser validates all twelve month grids and reads week-wide colour bands. Types now use canonical names; update filters and customisations using old labels.
