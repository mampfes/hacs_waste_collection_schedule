# Chichester District Council

Support for schedules provided by [Chichester District Council](https://www.chichester.gov.uk/checkyourbinday), serving the borough of Chichester, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: chichester_gov_uk
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
    - name: chichester_gov_uk
      args:
        uprn: 010002476348
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.