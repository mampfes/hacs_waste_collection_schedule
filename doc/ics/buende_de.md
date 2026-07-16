# Stadt Bünde

Stadt Bünde is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.buende.de/Stadtleben/Umwelt-I-Klima/Abfall/Abfallkalender-online/> and select your street.
- Right-click "Export in Kalenderanwendung" and copy the link address to get an ICAL link.
- Use this link as the `url` parameter.
- Replace the year (`vJ=2025`) with `{%Y}` in the URL.
- You may want to set the `regex` parameter to "BÜ (.*): Bünde" to get better titles.

## Examples

### Adalbert-Stifter-Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "B\xDC (.*): B\xFCnde"
        url: https://www.buende.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.3&strasse=2619.2.1&vtyp=2&vMo=1&vJ={%Y}&bMo=12
```
