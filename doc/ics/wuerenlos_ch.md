# Gemeinde Würenlos

Gemeinde Würenlos is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

Würenlos publishes a public iCalendar feed at
`https://www.wuerenlos.ch/fileadmin/00_website/entsorgungskalender/Entsorgungskalender_Wuerenlos_{%Y}.ics`.
Use this URL as the `url` parameter — `{%Y}` is replaced with the
current year automatically.

## Examples

### Würenlos

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.wuerenlos.ch/fileadmin/00_website/entsorgungskalender/Entsorgungskalender_Wuerenlos_{%Y}.ics
```
