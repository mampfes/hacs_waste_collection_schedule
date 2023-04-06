# FES Frankfurter Entsorgungs- und Service GmbH

FES Frankfurter Entsorgungs- und Service GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.fes-frankfurt.de/services/abfallkalender> and select your location.  
- Click on `Kalender`.
- Copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Achenbachstr. 2

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*)\s+\|
        split_at: ' / '
        url: https://www.fes-frankfurt.de/abfallkalender/QWNoZW5iYWNoc3RyLnwyfDYwNTk2.ics
```
