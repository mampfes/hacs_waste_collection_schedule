# Rova

Support for schedules provided by [Rova](https://www.rova.nl).

Source for Rova waste collection in the Netherlands.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rova_nl
      args:
        postalcode: POSTALCODE
        house_number: HOUSE_NUMBER
        addition: ADDITION
```

### Configuration Variables

**postalcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

**addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rova_nl
      args:
        postalcode: 8148PC
        house_number: '44'
```

## How to get the source arguments

Use the same postal code and house number you would enter at https://www.rova.nl/afvalkalender. If your address has a letter or addition, provide it in the 'addition' field.
