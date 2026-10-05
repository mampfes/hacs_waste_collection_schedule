# Simbio

Support for schedules provided by [Simbio](https://www.simbio.si/).

Source for Simbio.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: simbio_si
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
    - name: simbio_si
      args:
        street: Ljubljanska cesta
        house_number: 1 A
```
