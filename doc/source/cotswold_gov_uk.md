# Cotswold District Council

Support for waste collection schedules provided by [Cotswold District Council](https://www.cotswold.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cotswold_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

The full address string exactly as returned by the address lookup on the waste collection enquiry page.

## How to find your `address`

1. Go to the [Cotswold District Council waste collection enquiry page](https://community.cotswold.gov.uk/s/waste-collection-enquiry).
2. Start typing your postcode or street name into the address lookup field.
3. Select your property from the autocomplete suggestions.
4. Use the full address string exactly as it appears in the suggestion (including the postcode), for example `10 HAVEN HILL, CIRENCESTER, GL7 1BN`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cotswold_gov_uk
      args:
        address: "10 HAVEN HILL, CIRENCESTER, GL7 1BN"
```
