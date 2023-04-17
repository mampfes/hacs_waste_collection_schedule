# Blaue Tonne - Schlaue Tonne

Blaue Tonne - Schlaue Tonne is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.blauetonne-schlauetonne.de/abfuhrkalender> and select your location.
 - Right-click on `iCal Download` link and copy link address.
 - Replace the `url` in the example configuration with this link.
 - Replace the year in the url with `{%Y}`.

## Examples

### Altlußheim

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.blauetonne-schlauetonne.de/abfuhrkalender/{%Y}/altlussheim-altlussheim-1668.ics
```
