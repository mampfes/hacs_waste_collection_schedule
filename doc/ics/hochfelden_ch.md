# Gemeinde Hochfelden

Gemeinde Hochfelden is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

Hochfelden publishes public ICS feeds via the Mondstaub calendar platform.
Use the combined URL below as the `url` parameter. `{%Y}` is replaced with
the current year automatically.

Individual waste-type feeds are also available:
- Kehricht only: `https://hochfelden.ch/files/content/aktuelles/{%Y}/Entsorgungskalender/kehricht-hochfelden-{%Y}.ics`
- Grüngut only: `https://hochfelden.ch/files/content/aktuelles/{%Y}/Entsorgungskalender/gruengut-hochfelden-{%Y}.ics`
- Karton only: `https://hochfelden.ch/files/content/aktuelles/{%Y}/Entsorgungskalender/karton-sammlung-hochfelden-{%Y}.ics`
- Altpapier only: `https://hochfelden.ch/files/content/aktuelles/{%Y}/Entsorgungskalender/altpapier-sammlung-hochfelden-{%Y}.ics`

## Examples

### Hochfelden - alle Termine

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://hochfelden.ch/files/content/aktuelles/{%Y}/Entsorgungskalender/entsorgung-hochfelden-{%Y}-alle%20Termine.ics
```
