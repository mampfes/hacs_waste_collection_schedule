# ENNI Energie & Umwelt Niederrhein (Moers)

ENNI Energie & Umwelt Niederrhein (Moers) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://abfallkalender.enni.de> and find your street name.
- The URL is `https://abfallkalender.enni.de/ics-kalender/{street}` where `{street}` is your street name in lowercase without umlauts (e.g. `ae` instead of `ä`, `ss` instead of `ß`).

## Examples

### Hedwigstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallkalender.enni.de/ics-kalender/hedwigstrasse
```
### Bahnhofstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallkalender.enni.de/ics-kalender/bahnhofstrasse
```
