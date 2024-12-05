# Abfallkalender Würzburg (ICS)

Abfallkalender Würzburg (ICS) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.wuerzburg.de/themen/umwelt-klima/abfall-und-stadtreinigung/abfallkalender> and select your street.
- Click on "Calendar as ICS"
- Right-lick on "Download" and select "Copy link address"
- Use this link as URL parameter

## Examples

### Residenzplatz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.wuerzburg.de/themen/umwelt-klima/abfall-und-stadtreinigung/abfallkalender/ics?ev[addr]=19935
```
### Friedrich-Ebert-Ring ab 13

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.wuerzburg.de/themen/umwelt-klima/abfall-und-stadtreinigung/abfallkalender/ics?ev[addr]=19943
```
