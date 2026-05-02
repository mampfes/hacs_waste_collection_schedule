# Abfuhrtermine.info

Abfuhrtermine.info is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- The abfuhrtermine.info website of your region (list below).
- select your location.
- Right click -> copy link address on the "Termine als ICS-Datei zum Import in Terminverwaltungssoftware/MobiltelefonKalender" button.
- Use this link as the `url` parameter.

### List of available regions

- Attendorn: https://attendorn.abfuhrtermine.info/
- Drolshagen: https://drolshagen.abfuhrtermine.info/
- Finnentrop: https://finnentrop.abfuhrtermine.info/
- Kreuztal: https://kreuztal.abfuhrtermine.info/
- Lennestadt: https://lennestadt.abfuhrtermine.info
- Olpe: https://olpe.abfuhrtermine.info
- Wenden: https://wenden.abfuhrtermine.info

and maybe some more.

## Examples

### Olpe Gerstenhagen - Griesemert

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://olpe.abfuhrtermine.info/dates/exportDates/58/Ics
```
### Lennestadt Adlerstraße - Saalhausen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://lennestadt.abfuhrtermine.info/dates/exportDates/3232/Ics
```
