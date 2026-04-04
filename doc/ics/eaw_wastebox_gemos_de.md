# EAW Sangerhausen (Gemos)

EAW Sangerhausen (Gemos) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to the EAW Sangerhausen waste calendar at <https://eaw.wastebox.gemos-management.de>.
- Select your area and find the ICS download link.
- Use this URL as the `url` parameter.

## Examples

### Sangerhausen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://eaw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2025/List/330007/1489,1490,1491,1492,1493,1494,1495,1496,1497/190/Print/ics/Default/Abfuhrtermine.ics
```
