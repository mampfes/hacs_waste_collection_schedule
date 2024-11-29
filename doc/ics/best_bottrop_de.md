# BEST - Bottrop

BEST - Bottrop is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.best-bottrop.de/abfuhrtermine-0910213539.html> and select your location.  
- Click on `Termine für Kalender exportieren` then `Kalender abonnieren` to get an ical subscription link.
- Use this link as the `url` parameter.

## Examples

### Hauptstraße 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.best-bottrop.de/abfuhrkalender?format=ical&street=9CBCBFFF&number=1
```
