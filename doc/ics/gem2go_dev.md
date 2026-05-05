# gem2go (Abfallverband)

gem2go (Abfallverband) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to your municipality's gem2go waste calendar page or use the Abfallooe app.
- Find the iCal/ICS export link.
- The URL typically follows the pattern `https://uwpio.gem2go.dev/ical/{id1}/{id2}/{id3}`.
- Copy the full URL and use it as the `url` parameter.

## Examples

### Abfallverband OO

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://uwpio.gem2go.dev/ical/20151/280664/387228
```
