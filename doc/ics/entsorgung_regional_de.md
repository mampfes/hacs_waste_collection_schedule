# Abfallwirtschaft Enzkreis

Abfallwirtschaft Enzkreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfallwirtschaft-enzkreis.de/entsorgung/leerungstermine/terminservice-ics-datei.html> and select your location.  
- Select all waste types (or at least the ones you want to be reminded of).
- Replace the `url` in the example configuration with this link. 
- Do not forget the method and params parameter.

## Examples

### Engelsbrand

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          ICS_DOWNLOAD: 3def184ad8f4755ff269862ea77393dd
        url: "https://www.abfallwirtschaft-enzkreis.de/entsorgung/leerungstermine/terminservice-ics-datei.html?icsgemeinde=Engelsbrand&icsortsteil=Salmbach&icsabfallart[]=Bioabfall&icsabfallart[]=Elektrogro\xDF\
          ger\xE4te&icsabfallart[]=Glas&icsabfallart[]=LVP&icsabfallart[]=Papier&icsabfallart[]=Restm\xFC\
          ll&icsabfallart[]=Schadstoff&icsabfallart[]=Sperrm\xFCll"
```
### Neuhausen - Schellbronn

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          ICS_DOWNLOAD: 3def184ad8f4755ff269862ea77393dd
        url: https://www.abfallwirtschaft-enzkreis.de/entsorgung/leerungstermine/terminservice-ics-datei.html?icsgemeinde=Neuhausen&icsortsteil=Schellbronn&icsabfallart%5B%5D=Glas&icsabfallart%5B%5D=LVP&icsabfallart%5B%5D=Papier&icsabfallart%5B%5D=Restm%C3%BCll
```
