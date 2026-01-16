# Kredsløb

Kredsløb is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.kredslob.dk/produkter-og-services/genbrug-og-affald/affaldsbeholdere/toemmekalender> and select your location.  
- Click on `Abonnér på kalender` to get a ical subscription url.
- Use this link as the `url` parameter.

## Examples

### Skovparken 5, 8240 Risskov

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://portal-api.kredslob.dk/api/calendar/icsfeed/07517381___5_______/67799
```
### Skødstrupbakken 67, 8541 Skødstrup

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://portal-api.kredslob.dk/api/calendar/icsfeed/07517484__79_______/71319
```
