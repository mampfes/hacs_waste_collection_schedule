# Gipsprojekt

Gipsprojekt is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

Known to work with:

| Region | URL |
| ------ | --- |
| Stadtwerke Speyer | <https://www.stadtwerke-speyer.de/muellkalender> |
| Stadtwerke Aschaffenburg | <https://www.stwab.de/Abfall-Stadtreinigung/Muellabfuhr/Abfuhrtermine-und-Bezirk/> |


## How to get the configuration arguments

- Go to the collection schedule URL of your service provider (like <https://www.stadtwerke-speyer.de/muellkalender>) and click on your location/street.
- Right-click the "Im iCalendar-Format abonnieren/speichern" link on the bottom half of the page and copy the URL.
- Use this URL as the `url` parameter
- Check the URL for any year. In the case of Speyer, it is the case in the `Abfuhrkalender` and `Jahr` argument. Replace it with `{%Y}` as seen in the example configuration. This way the year will be automatically updated.

## Examples

### Speyer, Schnaudigelweg (Abfallgebiet Hellgrün)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stadtwerke-speyer.de/speyerGips/Gips?SessionMandant=Speyer&Anwendung=Abfuhrkalender&Methode=TermineAnzeigenICS&Mandant=Speyer&Abfuhrkalender=Speyer{%Y}&Bezirk_ID=22&Jahr={%Y}
```
### Aschaffenburg, Schillerstraße (bis Hs.Nrn. 108)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stwab.de/aschaffenburgGips/Gips?SessionMandant=Aschaffenburg&Anwendung=Abfuhrkalender&Methode=TermineAnzeigenICS&Mandant=Aschaffenburg&Abfuhrkalender=Aschaffenburg&Bezirk_ID=1647&Jahr={%Y}
```
