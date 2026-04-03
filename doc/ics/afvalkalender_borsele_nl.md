# Gemeente Borsele

Gemeente Borsele is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://afvalkalender.borsele.nl> and search for your address.
- Find the iCal download link.
- The URL follows the pattern: `https://afvalkalender.borsele.nl/afval/afvalkalender/{year}/{postcode}-{number}.ics`
- Replace the year with `{%Y}` for automatic year substitution.
- Use this URL as the `url` parameter.

## Examples

### Borsele 4451CM-12

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://afvalkalender.borsele.nl/afval/afvalkalender/{%Y}/4451CM-12.ics
```
