# Knowsley Council

Support for schedules provided by [Knowsley Council](https://www.knowsley.gov.uk/).

Source for Knowsley Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: knowsley_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: knowsley_gov_uk
      args:
        postcode: L364AR
        uprn: 000040082756
```

## How to get the source arguments

Enter your postcode and your property's UPRN (find it at https://www.findmyaddress.co.uk/).
