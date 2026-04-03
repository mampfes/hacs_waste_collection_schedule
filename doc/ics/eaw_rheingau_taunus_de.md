# EAW Rheingau-Taunus-Kreis

EAW Rheingau-Taunus-Kreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.eaw-rheingau-taunus.de/abfallsammlung/abfuhrtermine/>.
- Search for your street.
- Find the ICS/iCal download link.
- The URL follows the pattern: `https://www.eaw-rheingau-taunus.de/abfallsammlung/abfuhrtermine/ics/{street-id}/feed.ics`
- Use this URL as the `url` parameter.

## Examples

### Hessenstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eaw-rheingau-taunus.de/abfallsammlung/abfuhrtermine/ics/hessenstrasse-382/feed.ics
```
