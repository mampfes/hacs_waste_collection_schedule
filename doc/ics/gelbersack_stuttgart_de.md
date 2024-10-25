# Gelber Sack Stuttgart

Gelber Sack Stuttgart is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.gelbersack-stuttgart.de/abfuhrplan/> and select your location.  
- Right click -> copy the url of the `Termine in meinen Kalender eintragen` button.
- Replace the `url` in the example configuration with this link.

## Examples

### An der Burg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.gelbersack-stuttgart.de/abfuhrplan/export/an-der-burg?type=201
```
