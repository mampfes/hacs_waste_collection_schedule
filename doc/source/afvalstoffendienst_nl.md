# Afvalstoffendienst.nl

Support for schedules provided by [Afvalstoffendienst.nl](https://www.afvalstoffendienst.nl/).

Source for 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: afvalstoffendienst_nl
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
        addition: ADDITION
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

**addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: afvalstoffendienst_nl
      args:
        postcode: 5061AA
        house_number: '1'
```

## How to get the source arguments

Enter the postcode, house number and (optional) addition of your home address.
