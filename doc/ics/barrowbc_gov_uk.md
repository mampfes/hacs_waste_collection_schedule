# Westmorland & Furness Council, Barrow area

Westmorland & Furness Council, Barrow area is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://ww.barrowbc.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule> and select your location.  
- Right click -> copy the url of the `Add to iCalendar` link.
- Replace the `url` in the example configuration with this link. (If you know your UPRN, you can just replace the last part of the url with it.)
- if you want to shorten your entry names use the `regex` line from the second example (`Grey lidded bins for General waste` will show up as `Grey`)

## Examples

### 12 GLEASTON AVENUE, BARROW-IN-FURNESS, LA13 0BP

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://barrowbc.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/36022299
```
### SHORTENED, DALTON-IN-FURNESS, LA15 8HB

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) lidded .*
        url: https://barrowbc.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/36032299
```
