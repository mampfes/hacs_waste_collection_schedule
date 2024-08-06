# Rd4

Support for schedules provided by [Rd4](https://rd4.nl/), serving multiple municipalities in the Netherlands.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rd4_nl
      args:
        postal_code: POSTAL CODE (postcode)
        house_number: "HOUSE NUMBER (huisnummer)"
        
```

### Configuration Variables

**postal_code**  
*(String) (required)*

**house_number**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rd4_nl
      args:
        postal_code: 6417 AT
        house_number: "32"
        
```

## How to get the source argument

Use your postal code and house number. You can verify that your parameter are valid by entering them in the form at the [Rd4 website](https://mijn.rd4.nl/afvalkalender).
