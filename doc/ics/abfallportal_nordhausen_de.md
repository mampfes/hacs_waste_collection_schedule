# Abfallwirtschaft Landkreis Nordhausen

Abfallwirtschaft Landkreis Nordhausen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to Entsorgungskalender
- Select your village and street
- Right click the button '.ics-Datei Herunterladen'
- Replace the `url` in the example configuration with this link.

## Examples

### Nordhausen-Grimmelallee

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallportal-nordhausen.de/api/public/calendar/ics?addressid=548
```
