# Bamberg (Stadt und Landkreis)

Bamberg (Stadt und Landkreis) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfalltermine-bamberg.de/> and select your location.  
- Copy the link of the Herunterladen button below Digitaler Kalender.
- Replace the `url` in the example configuration with this link.

## Examples

### Schlüsselfeld - Thüngbach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.abfalltermine-bamberg.de/Bamberg/Landkreis/Schl%C3%BCsselfeld%20-%20Th%C3%BCngbach/ics
```
