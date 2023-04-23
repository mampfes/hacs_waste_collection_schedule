# Gelsendienste Gelsenkirchen

Gelsendienste Gelsenkirchen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.gelsendienste.de/privathaushalte/abfallkalender> and select your location.  
- Click on `Abfallkalender abonnieren` to open a sub-frame, and then copy the link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Adamshof 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://gelsendienste.abisapp.de/abfuhrkalender?format=ical&street=1A533A82&number=1
```
