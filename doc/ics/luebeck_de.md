# Lübeck Entsorgungsbetriebe

Lübeck Entsorgungsbetriebe is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://insert-it.de/BMSAbfallkalenderLuebeck> and select your location.  
- Right-click on `iCalendar` and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url with `{%Y}`.

## Examples

### Dampfpfeife 2

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://insert-it.de/BMSAbfallkalenderLuebeck/Main/Calender?bmsLocationId=127863&year={%Y}
```
