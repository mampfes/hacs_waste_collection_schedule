# EDG Entsorgung Dortmund

EDG Entsorgung Dortmund is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.edg.de/de/entsorgungsdienstleistungen/rein-damit/info-service/ical-webcal.htm?Submit1=Kalender+abonnieren> and select your location.  
- Click on `Kalender erzeugen`.
- Set `Wann möchten Sie erinnert werden?` to `Am Abfuhrtag`.
- Below `Outlook und weitere` set `Erinnerung` to `Keine Erinnerung`.
- Click on `Link kopieren` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Baackweg 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.edg.de/ical/kalender.ics?Strasse=Hanfweg&Hausnummer=1&Erinnerung=-1&Abfallart=1,2,3,4
```
