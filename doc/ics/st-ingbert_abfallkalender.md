# Abfallentsorgung Stadt St. Ingbert

Abfallentsorgung Stadt St. Ingbert is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://st-ingbert.mein-abfallkalender.online/app/webcal.html> and select your location/street/address.
- Select the options which you want to use, e.g. "Erinnerungen", etc.
- For the option "Verwendung" select "Termine via WebCal-Protokoll abonnieren (Allgemein)"
- Click on `Termine via iCal/WebCal nutzen`
- This will redirect you to the page where you get the required ICS URL. Select the URL under "WebCal-Adresse (webcal):"
- Right click on the URL and copy the link address.
- Replace the `url` in the example configuration.yaml with this link.

## Examples

### Fuldatal (area 1)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "webcal://st-ingbert.mein-abfallkalender.online/ical.ics?sid=8226&cd=inline&ft=6&fu=webcal_other&fp=next_30&wids=157,155,156,154,158&uid=167051&pwid=3fe0748bd9&cid=25"
      calendar_title: "Abfallkalender"
      customize:
        - type: "Rest Waste"
          alias: "Restmüll"
          icon: "mdi:trash-can"
        - type: "Paper Waste"
          alias: "Altpapiertonne"
          icon: "mdi:newspaper"
        - type: "Gelber Sack"
          alias: "Gelber Sack (DSD)"
          icon: "mdi:recycle"
        - type: "Biotonne"
          alias: "Biotonne"
          icon: "mdi:compost"
```
