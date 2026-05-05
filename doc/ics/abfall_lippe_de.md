# Abfall Lippe

Abfall Lippe is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://abfall-lippe.de> and find the waste collection calendar for your area.
- Right-click the ICS download link and copy the URL.
- Use this URL as the `url` parameter.

## Examples

### Blomberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfall-lippe.de/wp-content/uploads/2024/12/Blomberg-2025.ics
```
