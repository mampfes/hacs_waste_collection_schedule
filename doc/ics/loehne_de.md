# Stadt Löhne

Stadt Löhne is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.loehne.de/Leben-Entdecken/Stadtinfos/Abfall-/Abfallkalender/> and select your street.
- Copy the link of `Export in Kalenderanwendung`
- Use this link as the `url` parameter.
- Replace the year in the `url` with `{%Y}`.
  This will be replaced by the current year.
- you might want to keep the regex as it removes the city name from the title.

## Examples

### Ackerweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "(.*?): L\xF6hne"
        url: https://www.loehne.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.4&strasse=430.1.1&vtyp=2&vMo=01&vJ={%Y}&bMo=12
```
### Bahnhofstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "(.*?): L\xF6hne"
        url: https://www.loehne.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.4&strasse=430.110.1&vtyp=2&vMo=01&vJ={%Y}&bMo=12
```
### Königstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "(.*?): L\xF6hne"
        url: https://www.loehne.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.4&strasse=430.419.1&vtyp=2&vMo=01&vJ={%Y}&bMo=12
```
