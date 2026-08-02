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
        url: https://www.loehne.de/output/abfall_export.php?csv_export=1&amp;mode=vcal&amp;ort=393.4&amp;strasse=430.197.1&amp;vtyp=4&amp;vMo=1&amp;vJ=2026&amp;bMo=12
        year_field: vJ
```
### Kirchhain Grossseelheim

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchhain.de/output/abfall_export.php?csv_export=1&amp;mode=vcal&amp;ort=2848.6&amp;strasse=2848.158.1&amp;vtyp=2&amp;vMo=01&amp;vJ=2025&amp;bMo=12
        year_field: vJ
```
### Stadt Vlotho Topsundernweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.vlotho.de/output/abfall_export.php?csv_export=1&amp;mode=vcal&amp;ort=393.8&amp;strasse=3136.359.1&amp;abfart%5B0%5D=3136.1&amp;abfart%5B1%5D=3136.2&amp;abfart%5B2%5D=3136.3&amp;abfart%5B3%5D=3136.4&amp;abfart%5B4%5D=3136.5&amp;vtyp=1&amp;vMo=01&amp;vJ=2026&amp;bMo=12
        year_field: vJ
```
### Gemeinde Rödinghausen Studieker Weg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params: {}
        url: https://www.roedinghausen.de/output/abfall_export.php?csv_export=1&amp;mode=vcal&amp;ort=393.1&amp;strasse=521.244.1&amp;vtyp=2&amp;vMo=01&amp;vJ=2026&amp;bMo=12
        year_field: vJ
```
