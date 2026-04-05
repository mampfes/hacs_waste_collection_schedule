# Vlotho

Vlotho is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.vlotho.de/Leben-in-Vlotho/Abfallkalender-online/> and select your street.
- Right-click the "Export in Kalenderanwendung" link and copy the URL.
- Find the `strasse` parameter value in the URL (e.g. `3136.93.1` for Burgstraße).
- Use this value as the `strasse` parameter below.

## Examples

### Burgstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          bMo: '12'
          csv_export: '1'
          mode: vcal
          ort: '393.8'
          strasse: 3136.93.1
          vMo: '01'
          vtyp: '1'
        url: https://www.vlotho.de/output/abfall_export.php
        year_field: vJ
```
