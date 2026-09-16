# City of Yarra

Support for schedules provided by [City of Yarra](https://www.yarracity.vic.gov.au).

Source for City of Yarra waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        address: 201 Napier Street, Fitzroy VIC 3065
```

## How to get the source arguments

Enter your full street address including suburb and postcode, e.g. '333 Bridge Road, Richmond VIC 3121'.
