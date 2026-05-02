# Allensbach am Bodensee

Allensbach am Bodensee is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.gemeinde-allensbach.de/wohnen-leben/abfuhrkalender> and select your location.  
- Right-click on the link to the calendar below "Müll-Abfuhrtermine als Kalender-Datei" and copy the link address.
- Use this URL as the `url` parameter.
- You can replace the year in the URL with `{%Y}` so the calendar works for the current year (if they do not update the URL structure).

## Examples

### gemeinde_gesamt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.gemeinde-allensbach.de/fileadmin/Dateien/Website/Dateien/Abfall/Termine{%Y}.ics
```
