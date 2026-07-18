# Burgenländischer Müllverband

Support for schedules provided by [Burgenländischer Müllverband](https://www.bmv.at).

Source for BMV, Austria

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bmv_at
      args:
        ort: ORT
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bmv_at
      args:
        ort: ALLERSDORF
        strasse: HAUSNUMMER
        hausnummer: 9
```
