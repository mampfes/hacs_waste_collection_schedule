# Abfallwirtschaft Dithmarschen (AWD)

Abfallwirtschaft Dithmarschen (AWD) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.awd-online.de/abfuhrtermine/> and select your location.  
- You can either preselect your collection types now or modify them later using the customize option.
- Right click -> copy url the `Als Kalenderdatei (.ics) herunterladen` link.
- Replace the `url` in the example configuration with this link.

## Examples

### Nordhastedt Hauptsr. 24A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.awd-online.de/api_v2/collection_dates/1/ort/82/strasse/170/hausnummern/24A/abfallarten/R02-R04-R01-R21-B02-D02-P04-P02-P11-G0-W0/kalender.ics
```
