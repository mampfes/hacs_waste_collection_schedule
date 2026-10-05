# Monmouthshire Council

Support for schedules provided by [Monmouthshire Council](https://www.monmouthshire.gov.uk).

Source for Monmouthshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monmouthshire_gov_uk
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
    - name: monmouthshire_gov_uk
      args:
        uprn: 200000952833
```

## How to get the source arguments

You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering in your address details.
