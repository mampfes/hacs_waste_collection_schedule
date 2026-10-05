# Wirral Council

Support for schedules provided by [Wirral Council](https://wirral.gov.uk).

Source for wirral.gov.uk services for Wirral Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        address_value: ADDRESS_VALUE
        postcode: POSTCODE
```

### Configuration Variables

**address_value**  
*(string) (required)*

**postcode**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        postcode: CH49 4NP
        address_value: 000042037487
```

## How to get the source arguments

Go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, enter your postcode and select your address. The number at the end of the resulting web address (.../view/42119794) is your address value.
