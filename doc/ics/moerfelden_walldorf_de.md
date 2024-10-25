# Mörfelden-Walldorf

Mörfelden-Walldorf is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://abfallkalender.regioit.de/kalender-moerfelden-walldorf/index.jsp> and select your street.  
- Click on `Herunterladen (ICS)` and select `Keine Erinnerung`.
- Easy way (firefox):
  - Click on `Herunterladen (ICS)` to start the download.
  - Click on the download icon of Firefox and right click -> `Copy Download Link` on the ics file.
- Harder Way (All Browsers):
  - Open your browsers developer tools (F12) and go to the network tab.
  - Click on `Herunterladen (ICS)` and look for the request that is made to download the ics file.
  - Copy the URL of the request.
- Use this URL as `url` parameter.
- Replace the year in the URL with `{%Y}`, so it will be automatically replaced by the current year.

## Examples

### Aillaudstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://abfallkalender.regioit.de/kalender-moerfelden-walldorf/downloadfile.jsp?format=ics&zeit=-:00:00&lang=de&jahr={%Y}&ort=M\xF6\
          rfelden-Walldorf&strasse=8371&fraktion=0&fraktion=1&fraktion=2&fraktion=3&fraktion=4&fraktion=5&fraktion=6&fraktion=7&fraktion=8&fraktion=9&fraktion=10&fraktion=11&fraktion=12&md=-"
```
