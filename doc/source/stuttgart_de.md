# Abfall Stuttgart

Support for schedules provided by [Abfall Stuttgart](https://service.stuttgart.de).

Source for waste collections for the city of Stuttgart, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stuttgart_de
      args:
        street: STREET
        streetnr: STREETNR
```

### Configuration Variables

**street**  
*(string) (required)*

**streetnr**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stuttgart_de
      args:
        street: Im Steinengarten
        streetnr: 7
```
