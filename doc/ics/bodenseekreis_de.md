# Landratsamt Bodenseekreis

Landratsamt Bodenseekreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.bodenseekreis.de/umwelt-landnutzung/abfallentsorgung-privat/termine/abfuhrkalender/> and select your municipality.  
- Click on `iCal-Kalender` and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url with `{%Y}`.

## Examples

### Hagnau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.bodenseekreis.de/umwelt-landnutzung/abfallentsorgung-privat/termine/abfuhrkalender/export/2023/hagnau/1,4,2,5,16,7,9,8,10,6/ics/
```
