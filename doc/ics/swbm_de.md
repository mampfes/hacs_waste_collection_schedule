# Stadtwerke Bergheim

Stadtwerke Bergheim is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://swbm.de/geschaeftsfelder/abfallentsorgung/abfallkalender/> and find your district's waste collection calendar.
- Right-click the ICS download link for your district and copy the URL.
- Use this URL as the `url` parameter.

## Examples

### Bergheim

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://swbm.de/wp-content/uploads/2024/10/Bergheim.ics
```
