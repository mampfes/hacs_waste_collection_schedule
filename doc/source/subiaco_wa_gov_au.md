# City of Subiaco

Support for schedules provided by [City of Subiaco](https://www.subiaco.wa.gov.au).

Source for City of Subiaco, WA waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: subiaco_wa_gov_au
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
    - name: subiaco_wa_gov_au
      args:
        address: 241 Barker Road SUBIACO
```

## How to get the source arguments

Enter your street address including suburb (e.g. '241 Barker Road SUBIACO').
