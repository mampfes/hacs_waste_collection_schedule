# Landkreis Stade

Landkreis Stade is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://abfall.landkreis-stade.de/abfuhrkalender/> and select your location.  
- Right-click on `Als Kalenderdatei (.ics) herunterladen` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Dollern, an der Bahn 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfall.landkreis-stade.de/api_v2/collection_dates/1/ort/12/strasse/60/hausnummern/1/abfallarten/R02-R04-B02-D04-D12-P04-R14-R12-W0-R22-R24-R31/kalender.ics
```
