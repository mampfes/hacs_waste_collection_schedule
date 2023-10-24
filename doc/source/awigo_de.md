# AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH

Support for schedules provided by [AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH](https://www.awigo.de/), serving Landkreis Osnabrück, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: awigo_de
      args:
        ort: "ORT"
        strasse: STRAßE
        hnr: "HAUSNUMMER"
        
```

### Configuration Variables

**ort**  
*(String) (required)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

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

## How to get the source argument

Find the parameter of your address using [https://www.awigo.de/](https://www.awigo.de/) and write them exactly like on the web page.
