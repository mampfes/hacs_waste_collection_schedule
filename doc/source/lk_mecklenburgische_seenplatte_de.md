# Landkreis Mecklenburgische Seenplatte

Support for schedules provided by [Landkreis Mecklenburgische Seenplatte](https://www.lk-mecklenburgische-seenplatte.de).

Source for Landkreis Mecklenburgische Seenplatte waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lk_mecklenburgische_seenplatte_de
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
    - name: lk_mecklenburgische_seenplatte_de
      args:
        ort: Neubrandenburg
        strasse: "Atelierstra\xDFe"
```
