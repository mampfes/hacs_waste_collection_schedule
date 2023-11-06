# Landkreis Anhalt-Bitterfeld

Landkreis Anhalt-Bitterfeld is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abikw.de/kundenportal/abfalltourenplan> and select your location.  
- Click on `Exportieren iCal` and copy the link below `URL in Kalender-App einbinden`.
- Replace the `url` in the example configuration with this link.

## Examples

### Trüben

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abikw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2023/list/81779/565,566,567,568,569/Print/ics/Default/Abfuhrtermine.ics
```
