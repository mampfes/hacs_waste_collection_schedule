# ZBG Gladbeck

ZBG Gladbeck is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.zb-gladbeck.de/Abfuhrkalender-2326374551.html> and select your location.  
- Click on `Termine für Kalender exportieren`, then `Kalender abonnieren` to get the ical link.
- Use this url as `url` parameter.

## Examples

### Hauerweg 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zb-gladbeck.de/abfuhrkalender?format=ical&street=25689416&number=1
```
