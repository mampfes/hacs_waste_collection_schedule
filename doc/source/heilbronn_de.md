# Heilbronn Entsorgungsbetriebe

Support for schedules provided by [Heilbronn Entsorgungsbetriebe](https://heilbronn.de).

Source for city of Heilbronn, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: heilbronn_de
      args:
        plz: PLZ
        strasse: STRASSE
        hausnr: HAUSNR
```

### Configuration Variables

**plz**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hausnr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: heilbronn_de
      args:
        plz: 74072
        strasse: Rosenau
        hausnr: 33
```

## How to get the source arguments

Enter the postcode and street as they appear in the city of Heilbronn's waste calendar. The house number is only required for streets whose collection districts differ by house number.
