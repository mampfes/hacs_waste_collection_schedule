# Rother District Council

Support for schedules provided by [Rother District Council](https://www.rother.gov.uk).

Source for Rother District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rother_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rother_gov_uk
      args:
        uprn: 10002653856
```

## How to get the source arguments

Your UPRN is shown on https://www.rother.gov.uk once you look up your address under 'Your bin days'; you can also find it on https://www.findmyaddress.co.uk/.
