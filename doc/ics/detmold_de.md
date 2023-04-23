# Stadt Detmold

Stadt Detmold is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://abfuhrkalender.detmold.de/> and select your location.  
- Click on `Weitere Information`.
- Click on `Download ics-Datei (iCal).
- Right-click on `Download` link and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url with `{%Y}`.

## Examples

### Beateweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "M\xFCllabfuhr: (.*)"
        url: https://abfuhrkalender.detmold.de/icsmaker.php?strid=146&year={%Y}
```
