# Siegen

Siegen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.siegen-stadt.de/abfallkalender/> and select your location.  
- Right click -> copy link address on `Abfallkalender als iCAL` below `Druckansichten` to get the ics link.
- Replace the `url` in the example configuration with this link.
- Replace the year in the link with `{%Y}` to always get the current year.

## Examples

### HAUPTSTRAßE

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.siegen-stadt.de/abfallkalender/list/download/4130/{%Y}/0
```
