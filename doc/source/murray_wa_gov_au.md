# Shire of Murray

Support for schedules provided by [Shire of Murray](https://www.murray.wa.gov.au/).

Source for Shire of Murray waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: murray_wa_gov_au
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
    - name: murray_wa_gov_au
      args:
        address: 41 Wilson Road
```

## How to get the source arguments

Visit https://www.murray.wa.gov.au/waste-and-environment/waste-and-recycling/bins.aspx and search for your address to verify it is found.
