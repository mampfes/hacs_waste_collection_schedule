# City of Krems

City of Krems is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://awa.abfuhrtermine.at> and select your location.  
- Right click -> copy link address on the `Termine {YEAR}` button.
- Use this URL as the `url` parameter.

## Examples

### Krems an der Donau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awa.abfuhrtermine.at/webcalzip/Alt%20Rehberg/12/3500/30101
```
