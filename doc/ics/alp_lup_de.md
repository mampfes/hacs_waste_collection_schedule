# Aballwirtschaft Ludwigslust-Parchim AöR

Aballwirtschaft Ludwigslust-Parchim AöR is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://alp-lup.de/Service-Center/Abfuhrtermine/Abfallkalender/> and select your location.  
- Click on `Exportieren iCal` and copy the link below `URL in Kalender-App einbinden`.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url with `{%Y}` (as shown in the example).

## Examples

### Alt Brenz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://lwl.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/{%Y}/list/151002/1382,1383,1384,1385,1386,1387/61,64,68/Print/ics/Default/Abfuhrtermine.ics
```
