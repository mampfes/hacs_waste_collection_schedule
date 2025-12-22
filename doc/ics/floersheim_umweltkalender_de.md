# Flörsheim Am Main

Flörsheim Am Main is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.floersheim-umweltkalender.de/abfuhrtermine.html> and select your location.  
- Richt click -> copy link address on `Kalender für das ganze Jahr im iCal (ics) Format herunterladen` to get the ical link.
- Use this link as the `url` parameter.
- You might want to add regex `(.*?, .*?), .*?` to remove some unwanted information from the event title.

## Examples

### Hauptstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*?, .*?), .*?
        url: https://www.floersheim-umweltkalender.de/icalkalender.html?jahr=1&selectedmonat=&selectedwoche=&bezirk=1&hausnr=HausNr.&strasse=Hauptstra%C3%9Fe&checkedarts=1_10_3_7_4_8_9_5_6
```
