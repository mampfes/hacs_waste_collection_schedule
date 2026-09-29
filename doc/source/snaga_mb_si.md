# Snaga Maribor

Support for schedules provided by [Snaga Maribor](https://snaga-mb.si/).

Source for Snaga Maribor.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: snaga_mb_si
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: snaga_mb_si
      args:
        street: Ruska ulica
        house_number: 24
```
