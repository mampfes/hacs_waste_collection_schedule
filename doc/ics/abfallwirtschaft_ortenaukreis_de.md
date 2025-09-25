# Abfallwirtschaft Ortenaukreis

Abfallwirtschaft Ortenaukreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfallwirtschaft-ortenaukreis.de/abfallkalender-abfuhrtermine/abfallkalender-strauchgutabfuhrtermine> and select your location.
- Right-click on `ICS` and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the **2** year fields in the url with `{%Y}`.

## Examples

### Lahr - Vogesenstraße 1-17 + 4-14

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=ff692443f8b07d99f93674e9e0b6f529&mode=export&idhousenumber=720&wastetypes=66,177,951,33,347&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
### Offenburg - Ulmenweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=ff692443f8b07d99f93674e9e0b6f529&mode=export&idhousenumber=1347&wastetypes=66,177,951,33,347&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
### Rheinau - Rheinbischofsheim

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=ff692443f8b07d99f93674e9e0b6f529&mode=export&idhousenumber=1698&wastetypes=66,177,951,33,347&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
### Wolfach - Hauptstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=ff692443f8b07d99f93674e9e0b6f529&mode=export&idhousenumber=915&wastetypes=66,177,951,33,347&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
