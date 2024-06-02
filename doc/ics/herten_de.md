# Herten (durth-roos.de)

Herten (durth-roos.de) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://abfallkalender.durth-roos.de/herten/> and select your location.  
- Right click copy-url of the `iCalendar` button to get a webcal link. (You can ignore the note below as this source automatically refetches the ics file)
- Replace the `url` in the example configuration with this link.

## Examples

### Ackerstraße 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallkalender.durth-roos.de/herten/icalendar/Ackerstrasse_1.ics
```
