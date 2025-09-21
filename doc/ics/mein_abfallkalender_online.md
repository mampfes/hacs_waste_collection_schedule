# Mein-Abfallkalender.online

Mein-Abfallkalender.online is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- `mein-abfallkalender.online` uses a subdomain per supported municipality/city. Open the subdomain of your location, e.g., <https://eppstein.mein-abfallkalender.online>. If you not know the subdomain for your location, you can check their references page: <https://www.mein-abfallkalender.de/unsere_referenzen.html>.
- Select your location (if needed).
- Click on `Meine Termine anzeigen` [not on all regions].
- Click on `Termine (iCal / WebCal)` [not on all regions].
- Don't forget to register your e-mail, otherwise you will not get a valid webcal link!
- Click on `Termine via iCal/WebCal nutzen`.
- Copy the webcal link below `Online=Kalender "Google Kalender" (manuell)`.
- Use this url as the `url` parameter.

## Examples

### Eppstein, Niderjosbach, Bahnstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://eppstein.mein-abfallkalender.de/ical.ics?sid=19799&cd=inline&ft=noalarm&fu=webcal_google&fp=next_30&wids=494,495,496,498,497,499,502,500,513,501&uid=267293&pwid=1266c6e8df&cid=80
```
### St. Ingbert, Ackergasse, St. Ingbert-Mitte

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://st-ingbert.mein-abfallkalender.online/ical.ics?sid=8109&cd=inline&ft=6&fu=webcal_other&fp=next_30&wids=157,155,156,154,158&uid=167241&pwid=b3e6c5c670&cid=25
```
