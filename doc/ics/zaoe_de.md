# Zweckverband Abfallwirtschaft Oberes Elbtal

Zweckverband Abfallwirtschaft Oberes Elbtal is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.zaoe.de/abfallkalender/entsorgungstermine/abholtermine/> and select your location.  
- Click on `(als iCal-Abonnement)` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Riesa-Großenhain, Schönfeld, OT Kraußnitz, Grenzweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zaoe.de/kalender/ical/33213/_1-2-3-4-5-6-7/24/
```
