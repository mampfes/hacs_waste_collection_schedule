# East Lothian

Support for schedules provided by [East Lothian](https://www.eastlothian.gov.uk/).

Source for East Lothian waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastlothian_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eastlothian_gov_uk
      args:
        postcode: EH21 8GU
        address: 4 Laing Loan, Wallyford
```

## How to get the source arguments

Enter your postcode and your address as it appears in the address dropdown on https://www.eastlothian.gov.uk/waste-collection-schedule after searching for your postcode, e.g. '4 Laing Loan, Wallyford'. The postcode at the end of the entry may be left out.
