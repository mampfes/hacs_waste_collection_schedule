# Landkreis Wittmund

Support for schedules provided by [Landkreis Wittmund](https://www.landkreis-wittmund.de).

Source for Landkreis Wittmund waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_wittmund_de
      args:
        ort: ORT
        strasse: STRASSE
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_wittmund_de
      args:
        ort: Werdum
```
