# AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH

Support for schedules provided by [AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH](https://www.awigo.de/).

Source for AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awigo_de
      args:
        ort: ORT
        strasse: STRASSE
        hnr: HNR
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hnr**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awigo_de
      args:
        ort: Bippen
        strasse: Am Bad
        hnr: 4
```
