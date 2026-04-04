# Ginsheim-Gustavsburg

Ginsheim-Gustavsburg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.gigu.de/service-rathaus/dienstleistungen-online-rathaus/abfall/abfallkalender/> and select your district.
- Set `district` to your district number (`1` for Ginsheim, `2` for Gustavsburg).
- The `category` list selects which waste types to include (1-9 for all types). Adjust as needed.
- Set `dateFrom` and `dateTo` to the desired date range (format: `YYYY-MM-DD`).

## Examples

### Gustavsburg all categories

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          category:
          - '1'
          - '2'
          - '3'
          - '4'
          - '5'
          - '6'
          - '7'
          - '8'
          - '9'
          dateFrom: '2026-01-01'
          dateTo: '2026-12-31'
          district: '2'
        url: https://abfallkalender.gigu.de/export
```
### Ginsheim all categories

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          category:
          - '1'
          - '2'
          - '3'
          - '4'
          - '5'
          - '6'
          - '7'
          - '8'
          - '9'
          dateFrom: '2026-01-01'
          dateTo: '2026-12-31'
          district: '1'
        url: https://abfallkalender.gigu.de/export
```
