# Rushmoor Borough Council

Support for schedules provided by [Rushmoor Borough Council](https://www.rushmoor.gov.uk/recycling-rubbish-and-environment/bins-and-recycling/bin-collection-day-finder/), serving Rushmoor, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rushmoor_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rushmoor_gov_uk
      args:
        uprn: "100060551749"
```

## How to get the source argument
#  Find the UPRN of your address using https://www.findmyaddress.co.uk/search
