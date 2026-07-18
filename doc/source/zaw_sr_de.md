# ZAW-SR Straubing

Support for schedules provided by [ZAW-SR Straubing](https://www.zaw-sr.de).

Source for ZAW-SR (Zweckverband Abfallwirtschaft Straubing Stadt und Land).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zaw_sr_de
      args:
        city: CITY
        street: STREET
        hnr: HNR
        addition: ADDITION
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**hnr**  
*(string) (required)*

**addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zaw_sr_de
      args:
        city: Straubing
        street: Theresienplatz
        hnr: '1'
```
