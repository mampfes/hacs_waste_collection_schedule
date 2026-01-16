# Landkreis Anhalt-Bitterfeld

Landkreis Anhalt-Bitterfeld is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abikw.de/kundenportal/abfalltourenplan> and select your location.  
- Click on `Exportieren iCal` and copy the link below `URL in Kalender-App einbinden`.
- Use this link as the `url` parameter.
- Replace the year in the url with `{%Y}` (as shown in the example).

## Examples

### Trüben

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abikw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/{%Y}/list/82169/565,566,567,568,569/Print/ics/Default/Abfuhrtermine.ics
```
