# Gemeente Venray

Gemeente Venray is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://afvalkalender.venray.nl> and search for your address.
- Your BAG ID can be found by requesting `https://afvalkalender.venray.nl/adressen/{postcode}:{huisnummer}`.
- Use the URL `https://afvalkalender.venray.nl/ical/{BAG_ID}` as the `url` parameter.

## Examples

### Scheiweg 12 Leunen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://afvalkalender.venray.nl/ical/0984200000024569
```
