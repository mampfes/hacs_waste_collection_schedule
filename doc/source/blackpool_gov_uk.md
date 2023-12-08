# Blackpool Council

Support for schedules provided by [Blackpool Council](https://blackpool.gov.uk/Residents/), serving the town of Blackpool, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: blackpool_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
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
    - name: blackpool_gov_uk
      args:
        postcode: "FY1 4DZ"
        uprn: "100010802829"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
