# Enns

Support for schedules provided by [Enns](https://www.enns.at).

Waste collection schedule for Enns, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: enns_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: enns_at
      args:
        strasse: Am Damm
        hausnummer: '1'
```
