# Chorley Council

Support for schedules provided by [Chorley Council](https://www.chorley.gov.uk).

Source for chorley.gov.uk services for Chorley Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chorley_gov_uk
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
    - name: chorley_gov_uk
      args:
        postcode: PR6 7YD
        uprn: 010091497098
```

## How to get the source arguments

Go to https://www.chorley.gov.uk/bincollectiondays and enter your postcode. The UPRN is the option value of your address in the address dropdown (browser dev tools); an unknown UPRN is reported with the addresses the form lists for your postcode.
