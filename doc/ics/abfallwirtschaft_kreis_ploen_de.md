# Abfallwirtschaft Kreis Plön

Abfallwirtschaft Kreis Plön is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.kreis-ploen.de/Bürgerservice/Termine-Müllabfuhr/> and select your location.
- Select `Jahreskalender` as view
- Choose the types of waste you need
- Right-click on `Export in Kalenderanwendung` and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the year field in the url with `{%Y}`.

## Examples

### Bendfeld

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kreis-ploen.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=2156.6&strasse=2156.84.1&vtyp=4&vMo=1&vJ={%Y}&bMo=12
```
