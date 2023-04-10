# Zweckverband Abfallwirtschaft Region Hannover

Zweckverband Abfallwirtschaft Region Hannover is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Unfortunately you need a separate source for every waste type.
- Go to <https://www.aha-region.de/abholtermine/abfuhrkalender> and select your location.
- Open the inspection tools (`F12` or `rightclick -> inspect`).
- Open the network tab.
- Click on `Download Ical für Apple` below one pickup type you want to import.
- In the network tab you should now see a new request, click on it.
- Open the `Request` (Firefox) or `Payload` (Chromium) tab for this request.
- Replace the `strasse`, `hausnr`, `hausnraddon`, `ladeort` and`ical_apple` parameters with the payload data.
- You can add the other pickup types by adding additional sources and changing the `ical_apple` parameters: 10 = Restabfall, 33 = Leichtverpackung (Gelber Sack / Gelbe Tonne), 24 = Papier, 70 = Bioabfall (if theses values do not work you need to extract them like the other values)
- If you have multiple sources and want to use sensors remember to set `source_index` in your sensor config

## Examples

### Hannover Aalborghof / Wettbergen 1, Leichtverpackungen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          hausnr: '1'
          hausnraddon: ''
          ical_apple: '33'
          ladeort: 03253-0001
          strasse: 03253@Aalborghof / Wettbergen@Wettbergen
        url: https://www.aha-region.de/abholtermine/abfuhrkalender
```
### Hannover Aalborghof / Wettbergen 1, Restabfall

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          hausnr: '1'
          hausnraddon: ''
          ical_apple: '10'
          ladeort: 03253-0001
          strasse: 03253@Aalborghof / Wettbergen@Wettbergen
        url: https://www.aha-region.de/abholtermine/abfuhrkalender
```
