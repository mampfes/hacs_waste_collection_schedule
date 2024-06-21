# Kreis Steinburg

Kreis Steinburg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.steinburg.de/kreisverwaltung/informationen-der-fachaemter/amt-fuer-umweltschutz/abfallwirtschaft/abfuhrtermine/muellabfuhr.html> and select your location.  
- Right-click, copy the link address of the `Als Kalenderdatei (.ics) herunterladen` link.
- Replace the `url` in the example configuration with this link.

## Examples

### Bekmünde Am Deich 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfall.steinburg.de/api_v2/collection_dates/1/ort/10/strasse/10/hausnummern/1/abfallarten/R02-B02-P04-D02-R04-R11-W0/kalender.ics
```
