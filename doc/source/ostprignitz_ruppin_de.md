# Ostprignitz-Ruppin

Support for schedules provided by [Ostprignitz-Ruppin](https://www.ostprignitz-ruppin.de).

Source for Ostprignitz-Ruppin waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ostprignitz_ruppin_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**  
*(string) (required)*

**ort**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ostprignitz_ruppin_de
      args:
        ort: Neuruppin
        strasse: Am alten Gymnasium
```

## How to get the source arguments

Enter your street. If the street name exists in several places, add the place name to disambiguate.
