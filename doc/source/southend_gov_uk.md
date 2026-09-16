# Southend-on-Sea City Council

Support for schedules provided by [Southend-on-Sea City Council](https://www.southend.gov.uk).

Source for southend.gov.uk services for Southend-on-Sea City Council, UK.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: southend_gov_uk
      args:
        address: ADDRESS
        uprn: UPRN
```

### Using postcode

```yaml
waste_collection_schedule:
  sources:
    - name: southend_gov_uk
      args:
        address: ADDRESS
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**address**  
*(string) (optional)*

Provide one of: `uprn` or `postcode`.

## Example

### Using postcode

```yaml
waste_collection_schedule:
  sources:
    - name: southend_gov_uk
      args:
        address: 38 Thorpedene Gardens, Shoeburyness
        postcode: SS3 9JD
```

## How to get the source arguments

Provide your UPRN, or your postcode plus an address to match. Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address details.
