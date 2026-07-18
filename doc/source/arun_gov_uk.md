# Arun District Council

Support for schedules provided by [Arun District Council](https://www.arun.gov.uk).

Source for arun.gov.uk services for Arun District, UK.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: arun_gov_uk
      args:
        address: ADDRESS
        uprn: UPRN
```

### Using postcode

```yaml
waste_collection_schedule:
  sources:
    - name: arun_gov_uk
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
    - name: arun_gov_uk
      args:
        address: 21A Beach Road, Littlehampton
        postcode: BN17 5JA
```

## How to get the source arguments

Provide your UPRN, or your postcode plus an address to match. Find your UPRN at https://www.findmyaddress.co.uk/
