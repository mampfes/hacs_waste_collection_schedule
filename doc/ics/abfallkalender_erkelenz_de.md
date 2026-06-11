# Abfallkalender Erkelenz

Abfallkalender Erkelenz is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfallkalender-erkelenz.de> and select your district (Bezirk).
- Find your district number and use it in the `url` parameter below, replacing `BEZIRK` with your number.

## Examples

### Holzweiler (Bezirk 10)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.abfallkalender-erkelenz.de/ical?bezirk=10
```
