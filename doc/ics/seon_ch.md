# Seon

Seon is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Currently <https://www.seon.ch/verwaltung/dienstleistungen.html/21/service/370> provides only a PDF version of the waste schedule
- Because of this use the RAW link to the ics file within repository <https://github.com/starwarsfan/entsorgungskalender>
- Use <https://raw.githubusercontent.com/starwarsfan/entsorgungskalender/refs/heads/main/entsorgungskalender.ics> as the `url` parameter.

## Examples

### Oberdorfstrasse 11, 5703 Seon

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/starwarsfan/entsorgungskalender/refs/heads/main/entsorgungskalender.ics
```
