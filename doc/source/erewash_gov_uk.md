# Hart District Council

Support for schedules provided by [Erewash Borough Council](https://www.erewash.gov.uk/bins-and-recycling/when-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: erewash_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string | integer) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: erewash_gov_uk
      args:
        uprn: 100030118783
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.
