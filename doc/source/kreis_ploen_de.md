# Abfallwirtschaft Kreis Plön

Support for schedules provided by [Abfallwirtschaft Kreis Plön](https://www.kreis-ploen.de).

Source for Abfallwirtschaft Kreis Plön waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kreis_ploen_de
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
    - name: kreis_ploen_de
      args:
        strasse: "Hauptstra\xDFe"
        ort: "K\xF6hn"
```
