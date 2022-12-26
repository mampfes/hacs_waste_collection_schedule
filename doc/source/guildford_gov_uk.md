# Guildford Borough Council

Support for schedules provided by [Guildord Borough Council](https://my.guildford.gov.uk/customers/s/view-bin-collections), serving Guildford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: guildford_gov_uk
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
    - name: guildford_gov_uk
      args:
        uprn: "10007060305"
```

## How to get the source argument

Find the UPRN of your address using [https://www.findmyaddress.co.uk/search](https://www.findmyaddress.co.uk/search).
