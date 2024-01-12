# SWK Herford

SWK Herford is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://swk.herford.de/Entsorgung/Abfallkalender-/> and select your location.  
- Copy the link of `  Export in Kalenderanwendung`
- Replace the `url` in the example configuration with this link.
- Replace the year in the `url` with `{%Y}`.  
  This will be replaced by the current year.
- you might want to keep the regex as it removes potentially unnecessary information from the title.

## Examples

### Hauptstrasse 1 C

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "HF (.*?),? \\d{1} w\xF6chentlich.*"
        url: https://swk.herford.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.9&strasse=395.5.1&vtyp=2&vMo=01&vJ={%Y}&bMo=12
```
