# Hart District Council

Support for schedules provided by [Hart District Council](https://www.hart.gov.uk/waste-and-recycling/when-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hart_gov_uk
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
    - name: hart_gov_uk
      args:
        uprn: 100060420702
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.
Residential Addresses only. Some flat blocks are managed by trade waste companies.