# Abfallwirtschaftsbetrieb Ilm-Kreis

Support for schedules provided by [Abfallwirtschaftsbetrieb Ilm-Kreis](https://www.ilm-kreis.de).

Source for Abfallwirtschaftsbetrieb Ilm-Kreis waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ilm_kreis_de
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
    - name: ilm_kreis_de
      args:
        strasse: "Gerhart-Hauptmann-Stra\xDFe"
        ort: Arnstadt
```
