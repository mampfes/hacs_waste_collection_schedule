# Waidhofen an der Ybbs

Waidhofen an der Ybbs is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://m.abfuhrtermine.at/> and select your location.  
- Right click -> copy link address on the `Termine importieren` button.
- Use this URL as the `url` parameter.

## Examples

### Hauptplatz 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://m.abfuhrtermine.at/icalreminder/Hauptplatz/1/3340/30301
```
