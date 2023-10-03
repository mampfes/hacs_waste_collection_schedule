# EVA Abfallentsorgung

EVA Abfallentsorgung is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto https://www.eva-abfallentsorgung.de/Service-Center/Abfallentsorgung/Abfuhrkalender%20individuell#
- Choose Place and Location
- Click on ICS-Datei Kalender herunterladen
- Turn off Erinnerung and select Alarm Meldung anzeigen
- Copy the link of the download ICS
- Replace the url in the example configuration with this link

## Examples

### Ingenried

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: https://www.eva-abfallentsorgung.de/genics?ort=Ingenried&strasse=10477&strassenname=Ingenried&erinnerung=0&alarm=0&r=1&b=1&g=1&p=1&s=1
```
