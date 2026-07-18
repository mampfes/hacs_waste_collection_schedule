# City of Wanneroo

Support for schedules provided by [City of Wanneroo](https://www.wanneroo.wa.gov.au/).

Source for City of Wanneroo.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wanneroo_wa_gov_au
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
    - name: wanneroo_wa_gov_au
      args:
        address: 23 Bakana LP LANDSDALE
```

## How to get the source arguments

Enter your street address including suburb (e.g. '23 Bakana LP LANDSDALE').
