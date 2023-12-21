# Gipsprojekt

Gipsprojekt is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

known to work with: 
| region | url |
| ------ | --- |
| Heidelberg | <https://www.gipsprojekt.de/featureGips/Gips?Anwendung=Abfuhrkalender&Mandant=Heidelberg&Abfuhrkalender=Heidelberg> |


## How to get the configuration arguments

- Goto the Abfuhrkalender url of your service provider (like <https://www.gipsprojekt.de/featureGips/Gips?Anwendung=Abfuhrkalender&Mandant=Heidelberg&Abfuhrkalender=Heidelberg>) and click on your location/street.  
- Right-click -> copy the url of the Im iCalendar-Format abonnieren/speichern.
- Replace the `url` in the example configuration with this link.

## Examples

### Heidelberg Berthold-Mogel-Str. (Südstadt)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.gipsprojekt.de/featureGips/Gips?SessionMandant=Heidelberg&Anwendung=ABFUHRKALENDER&Methode=TermineAnzeigenICS&Mandant=Heidelberg&Abfuhrkalender=Heidelberg&Bezirk_ID=36413&Jahr=2023&Suchkriterium1=
```
