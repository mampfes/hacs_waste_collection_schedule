# Umweltv

Umweltv is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://abfallv.zerowaste.io/web-reminder> and select your location and waste types. 
- Click on `Kalender Bo/Download` and copy the URL below `Adresse zum Abonnieren`.
- Use this link as the `url` parameter.

## Examples

### Bürs

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallv.zerowaste.io/ical/3338?area_filter=324%2C325%2C326%2C327%2C328%2C329%2C1449%2C1512%2C2046%2C2822&reminder
```
### Andelsbuch Bergseite

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallv.zerowaste.io/ical/1899?area_filter=192%2C193%2C194%2C195%2C1440%2C1441%2C1442%2C1443%2C1466%2C2035%2C2847&reminder
```
