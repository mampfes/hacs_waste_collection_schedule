# Abfallwirtschaft Potsdam-Mittelmark (APM)

Abfallwirtschaft Potsdam-Mittelmark (APM) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.apm-niemegk.de/kundenservice/abfuhrtermine/> and select your location.  
- Click on `Exportieren iCal` to get a webcal link below `URL in Kalender-App einbinden`.
- Replace the `url` in the example configuration with this link.
- Replace the Year in the URL with `{%Y}`

## Examples

### Altbensdorf

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://apm.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/{%Y}/List/155643/1427,1429,1431,1433,1434,1435,1436,1437/180/Print/ics/Default/Abfuhrtermine.ics
```
