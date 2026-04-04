# Rivière-Beaudette

Rivière-Beaudette is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://riviere-beaudette.com/> and find the waste collection calendar under the "Calendriers" section.
- Download the ICS (.ics) calendar file.
- The ICS file URL typically follows the pattern: `https://riviere-beaudette.com/wp-content/uploads/{year}/01/CollectesRB{year}V2.ics`
- Use this URL as the `url` parameter, replacing the year with `{%Y}` for automatic year substitution.
- Use the `regex` parameter to extract waste types from event summaries.

## Examples

### Rivière-Beaudette

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: \s*Collecte (?:de la |du |des |de |la )?(.+?)\s*$
        url: https://riviere-beaudette.com/wp-content/uploads/{%Y}/01/CollectesRB{%Y}V2.ics
```
