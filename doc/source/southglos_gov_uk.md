# South Gloucestershire Council

Support for schedules provided by [South Gloucestershire Council](https://beta.southglos.gov.uk/waste-and-recycling-collection-date), serving the district of South Gloucestershire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southglos_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: southglos_gov_uk
      args:
        uprn: 639072
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.