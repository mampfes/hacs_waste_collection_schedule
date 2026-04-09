# Georgina (ON)

Georgina (ON) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.georgina.ca/living-here/garbage-recycling> and find your collection zone.
- Use the ICS URL format: `http://calendar.recyclecoach.com/calendar/export/586/GEO/zone-ZONE.ics`
- Replace `ZONE` with your zone ID (e.g. `z1890`).

## Examples

### Zone z1890

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ', '
        url: http://calendar.recyclecoach.com/calendar/export/586/GEO/zone-z1890.ics
```
