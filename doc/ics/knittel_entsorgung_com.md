# Knittel Entsorgung

Knittel Entsorgung is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.knittel-entsorgung.com> and find the waste collection calendar for your area.
- Right-click the ICS download link and copy the URL.
- Use this URL as the `url` parameter.

## Examples

### Nersingen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.knittel-entsorgung.com/wp-content/uploads/2025/11/NERSINGEN_Nersingen_Leibi_Ober-Unterfahlheim_Strass_2026.ics
```
