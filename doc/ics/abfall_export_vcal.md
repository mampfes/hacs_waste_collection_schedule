# Abfall Export (vCal)

Abfall Export (vCal) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to your municipality's waste collection calendar page.
- Look for an iCal/ICS export option.
- The URL typically contains `abfall_export.php?mode=vcal`.
- Copy the full URL and use it as the `url` parameter.

## Examples

### Stadt Löhne

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.loehne.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=393.4&strasse=430.197.1&vtyp=4&vMo=1&vJ=2026&bMo=12
        year_field: vJ
```
### Kirchhain Grossseelheim

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchhain.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=2848.6&strasse=2848.158.1&vtyp=2&vMo=01&vJ=2025&bMo=12
        year_field: vJ
```
