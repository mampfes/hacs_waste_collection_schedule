# Schwalbach am Taunus

Schwalbach am Taunus is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.schwalbach.de/Rathaus-und-Buergerservice/Buergerservice/Abfallentsorgung/Digitaler-Abfallkalender.htm> and navigate to the digital waste calendar.
- Select your street from the dropdown. Note your **Abfuhrbezirk** number (1–4) shown next to the street.
- Right-click on the yellow calendar download button (e.g. "Termine mit wöchentlicher Restmüll-Abholung für den Abfuhrbezirk 1 - 2026") and copy the link address.
- The link will look like: `https://www.schwalbach.de/city_data/assets/431/ical/2026_Abfuhrbezirk-1_woechentlich.ics`
- Replace the year (`2026`) with `{%Y}` and add `version: 1` to your config so the year is updated automatically.
- Use this modified link as the `url` parameter.

## Examples

### Abfuhrbezirk 1 wöchentlich

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.schwalbach.de/city_data/assets/431/ical/{%Y}_Abfuhrbezirk-1_woechentlich.ics
        version: 1
```
### Abfuhrbezirk 2 14-täglich

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.schwalbach.de/city_data/assets/431/ical/{%Y}_Abfuhrbezirk-2_14-taegig.ics
        version: 1
```
