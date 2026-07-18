# City of Vincent

Support for schedules provided by [City of Vincent](https://www.vincent.wa.gov.au).

Source for City of Vincent (WA) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vincent_wa_gov_au
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
    - name: vincent_wa_gov_au
      args:
        address: 8 Kadina St, North Perth WA 6006
```

## How to get the source arguments

Enter your street address within the City of Vincent (e.g. '8 Kadina St, North Perth WA 6006').
