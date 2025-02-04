# Stadt Enger

Stadt Enger is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.enger.de/Leben-in-Enger/Planen-Bauen-Wohnen/Abfall-Stra%C3%9Fenreinigung/Abfallkalender/> and select your Street.  
- Select `Jahreskalender` and the bin types you want to see (leave all unchecked to get all types).
- Right-click copy link address on the `Export in Kalenderanwendung` link to get a ICAL link.
- Use this link as `url` parameter.
- Replace the Year (`vJ=2025`) with `{%Y}` in the URL.
- You may want to set the `regex` parameter to "EN (.*): Enger" to get better titles.

## Examples

### Ringstr

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: 'EN (.*): Enger'
        url: https://www.enger.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.6&strasse=1470.581.1&vtyp=4&vMo=1&vJ={%Y}&bMo=12
```
