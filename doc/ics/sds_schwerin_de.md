# sds Schwerin

sds Schwerin is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.sds-schwerin.de/abfall-strassenreinigung/entsorgungskalender/> and select your location.  
- Click on `Exportieren iCal` and copy the link below `URL in Kalender-App einbinden`
- Use this link as `url` parameter.
- Rplace the year in the URL with `{%Y}`, which will be replaced by the current year.

## Examples

### Ahornstraße 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://sds.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/{%Y}/List/744769/779,780,781,782/54/Print/ics/Default/Abfuhrtermine.ics
```
