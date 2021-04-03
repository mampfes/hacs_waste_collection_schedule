# AbfallNavi.de

Support for schedules provided by [Abfallnavi.de](https://www.abfallnavi.de). The service is hosted under [regioit.de](https://regioit.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: SERVICE
        ort: SERVICE
        strasse: STRASSE
        hausnummer: hausnummer
```

### Configuration Variables

**service**<br>
*(string) (required)*

**ort**<br>
*(string) (required)*

**strasse**<br>
*(string) (required)*

**hausnummer**<br>
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: coe
        ort: Coesfeld
        strasse: Ahornweg
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfallnavi_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfallnavi_de.py).

Just run this script from a shell and answer the questions.
