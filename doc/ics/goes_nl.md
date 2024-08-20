# Goes

Goes is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://afvalkalender.goes.nl/> and select your location.  
- Right click copy link address on the `Persoonlijke afvalkalender` button.
- Replace the `url` in the example configuration with this link.
- Replace the current year with `{%Y}` in the link.

## Examples

### 4472AS 2

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://afvalkalender.goes.nl/{%Y}/4472AS-2.ics
```
