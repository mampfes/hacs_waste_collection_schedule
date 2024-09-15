# Stadt Spenge

Stadt Spenge is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.spenge.de/Rathaus-Politik/Allgemeines-Stadtservice/Abfall/Online-Abfall-Kalender/> and select your Street.  
- Select `Jahreskalender` and the bin types you want to see (leave all unchecked to get all types).
- Right-click copy link address on the `Export in Kalenderanwendung` link to get a ICAL link.
- Use this link as `url` parameter.
- Replace the Year (`vJ=2024`) with `{%Y}` in the URL.
- You may want to set the `regex` parameter to "SP (.*): Spenge" to get better titles.

## Examples

### Am Bahnhof

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: 'SP (.*): Spenge'
        url: https://www.spenge.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.5&strasse=1492.8.1&vtyp=4&vMo=1&vJ={%Y}&bMo=12
```
