# Heilbronn Entsorgungsbetriebe

Support for schedules provided by [heilbronn.de](https://www.heilbronn.de/).

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
*(integer | integer) (required)*

**strasse**  
*(string) (required)*

**hausnr**  
*(string | integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        plz: 74072
        abf_strasse: "Rosenau"
        abf_hausnr: 33
```

## How to get the source arguments

Use your PLZ, street and house number. You can check if [Abfallratgeber Heilbronn](https://abfallratgeber.heilbronn.de/#!/calendar) shows correct values, then use exactly the same spelling for your configuration.
