# Omrin

Support for schedules provided by [Omrin](https://www.omrin.nl).

Source for Omrin waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: omrin_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        suffix: SUFFIX
```

### Configuration Variables

**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: omrin_nl
      args:
        postal_code: 3851MA
        house_number: '3'
        suffix: ''
```

## How to get the source arguments

Enter the postcode, house number and, if you have one, the house number suffix of your address, as in the Omrin Afvalapp.
