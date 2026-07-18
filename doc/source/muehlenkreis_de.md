# Mühlenkreis Minden-Lübbecke

Support for schedules provided by [Mühlenkreis Minden-Lübbecke](https://www.muehlenkreis.de).

Source for Mühlenkreis Minden-Lübbecke waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muehlenkreis_de
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
    - name: muehlenkreis_de
      args:
        strasse: "Hauptstra\xDFe"
        ort: Harlinghausen
```
