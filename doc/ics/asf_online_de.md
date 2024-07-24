# Schleswig-Flensburg (ASF)

Schleswig-Flensburg (ASF) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.asf-online.de/abfuhrtermine/> and select your location.
- You may want to select the `Abfallarten` if you do not want all to show up in your calendar.
- Right click -> copy-link the `Als Kalenderdatei (.ics) herunterladen` button to get the ICS link.
- Replace the `url` in the example configuration with this link.

## Examples

### Dannewerk Katenweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.asf-online.de/api_v2/collection_dates/1/ort/19/strasse/100/hausnummern/1/abfallarten/R04-R02-B02-D02-P04-P44-P22-R44-R42-R11R21-R54-R52-R61-R71-R82-B82-P82-D82/kalender.ics
```
