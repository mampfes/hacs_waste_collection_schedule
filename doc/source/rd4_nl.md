# Rd4

Support for schedules provided by [Rd4](https://rd4.nl/).

Source for Rd4.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rd4_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        house_number_extension: HOUSE_NUMBER_EXTENSION
```

### Configuration Variables

**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_number_extension**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rd4_nl
      args:
        postal_code: 6417 AT
        house_number: 32
```
