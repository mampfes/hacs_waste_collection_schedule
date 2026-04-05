# Eupen

Eupen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.eupen.be/leben-in-eupen/abfall-recycling/abfallentsorgung/> and identify your zone.
- There are 3 zones: `oberstadt`, `unterstadt`, and `kettenis`.
- Use `{%Y}` in the URL to automatically replace the year.

## Examples

### Oberstadt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eupen.be/wp-content/uploads/digitaler-muellkalender-oberstadt-{%Y}-1.ics
```
### Unterstadt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eupen.be/wp-content/uploads/digitaler-muellkalender-unterstadt-{%Y}-1.ics
```
### Kettenis

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eupen.be/wp-content/uploads/digitaler-muellkalender-kettenis-{%Y}-1.ics
```
