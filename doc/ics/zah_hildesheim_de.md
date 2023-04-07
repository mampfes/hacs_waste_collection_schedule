# ZAH Hildesheim

ZAH Hildesheim is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.zah-hildesheim.de/termine/> and select your location.  
- Right-click on `Export Kalender` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Elze, Ortsteil Elze, Meisenweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*)(?:\s\(verschoben\))
        url: https://hildesheim.abfuhrkalender.de/ICalendar/Index.aspx?year={%Y}&streetID=5065
```
