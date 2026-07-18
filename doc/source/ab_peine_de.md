# Landkreis Peine

Support for schedules provided by [Landkreis Peine](https://ab-peine.de).

Source for Abfallwirtschaftsbetrieb Landkreis Peine waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
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
    - name: ab_peine_de
      args:
        strasse: "Gerhart-Hauptmann-Stra\xDFe"
```
