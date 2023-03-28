# Gateshead Council

Support for schedules provided by [Gateshead Council](https://www.gateshead.gov.uk/article/3150/Bin-collection-day-checker).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gateshead_gov_uk
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
    - name: gateshead_gov_uk
      args:
        uprn: 010070837598
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.
Residential Addresses only. Some flat blocks are managed by trade waste companies. 