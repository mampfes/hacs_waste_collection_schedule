# BMV.at

Support for schedules provided by [bmv.at](https://www.bmv.at/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bmv_at
      args:
        ort: ORT
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

To get the source arguments, open the [website](https://www.bmv.at/service/muellabfuhrtermine.html) and select the right values for your location.

Copy the values for `Ort`, `Straße` and `Hausnummer` into the configuration. Do not change to lower case! Just take the values as they are.

### Configuration Variables

**ORT**<br>
*(string) (required)*<br>
City

**STRASSE**<br>
*(string) (required)*<br>
Street

**HAUSNUMMER**<br>
*(string) (required)*<br>
Housenumber

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: bmv_at
      args:
        ort: BAD SAUERBRUNN
        strasse: BUCHINGERWEG
        hausnummer: 16
```
