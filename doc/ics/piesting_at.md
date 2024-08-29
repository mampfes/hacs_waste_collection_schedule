# Markt Piesting Dreistetten

Markt Piesting Dreistetten is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.piesting.at/muellentsorgung/>.  
- Right-click -> copy link address on the "Herunterladen" button below "digitaler Kalender".
- Replace the `url` in the example configuration with this link.

## Examples

### ICAL File

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.google.com/calendar/ical/7570b106hm2i4dibq23tes9p8c%40group.calendar.google.com/public/basic.ics
```
