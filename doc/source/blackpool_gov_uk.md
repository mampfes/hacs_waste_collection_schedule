# Blackpool Council

Support for schedules provided by [Blackpool Council](https://www.blackpool.gov.uk/Residents/Waste-and-recycling/Bin-collections/Bin-collections.aspx), serving the district of Blackpool, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blackpool_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: blackpool_gov_uk
      args:
        uprn: "200002844363"
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.
