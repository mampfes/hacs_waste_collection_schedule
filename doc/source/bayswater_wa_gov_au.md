# City of Bayswater

Support for schedules provided by [City of Bayswater](https://www.bayswater.wa.gov.au).

Source for City of Bayswater waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bayswater_wa_gov_au
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
    - name: bayswater_wa_gov_au
      args:
        address: 9 Wholley St Bayswater
```

## How to get the source arguments

Enter your street address including suburb (e.g. '9 Wholley St Bayswater').
