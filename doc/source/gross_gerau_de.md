# Kreisstadt Groß-Gerau

Support for schedules provided by [Kreisstadt Groß-Gerau](https://www.gross-gerau.de).

Source for Kreisstadt Groß-Gerau waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gross_gerau_de
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
    - name: gross_gerau_de
      args:
        strasse: "Adam-Rauch-Stra\xDFe"
        ort: "Gro\xDF-Gerau"
```
