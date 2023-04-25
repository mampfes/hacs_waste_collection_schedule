# Lebacher Abfallzweckverband (LAZ)

Lebacher Abfallzweckverband (LAZ) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.lebach.de/lebach/abfall/abfuhrkalender/> and select your location in the gray box on the right.  
- Right click on `hier: die Ical-Datei zum Importieren auf Ihr Mobiltelefon` select `copy link` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Hoxberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.lebach.de/fileadmin/Dokumente_und_Grafiken/Abfall/Ical_Dateien/Hoxberg.ics
```
