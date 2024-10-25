# Afval Wijzer

Afval Wijzer is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.mijnafvalwijzer.nl> and search for your location.  
- Click on the calendar icon button to get a webcal link.
- Use this url as the `url` parameter.

## Examples

### Tulpenburg 61 Amstelveen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.mijnafvalwijzer.nl/webservices/ical/11f68080-fdd0-44cf-a77b-043bc11e833d
```
