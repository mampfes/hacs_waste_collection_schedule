# Circulus

Support for schedules provided by [Circulus.nl](https://www.circulus.nl/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: circulus_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables
**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
   - name: circulus_nl
      args:
        postal_code: 7206AC
        house_number: 1
```
