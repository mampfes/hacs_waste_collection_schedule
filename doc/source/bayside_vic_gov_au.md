# Bayside Council (Victoria)

Support for schedules provided by [Bayside Council (Victoria)](https://bayside.vic.gov.au).

Source for Bayside Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bayside_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bayside_vic_gov_au
      args:
        street_address: 76 Royal Avenue Sandringham
```

## How to get the source arguments

Enter your street address including suburb.
