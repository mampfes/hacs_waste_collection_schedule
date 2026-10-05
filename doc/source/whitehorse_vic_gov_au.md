# Whitehorse City Council

Support for schedules provided by [Whitehorse City Council](https://www.whitehorse.vic.gov.au).

Source for Whitehorse City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: whitehorse_vic_gov_au
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
    - name: whitehorse_vic_gov_au
      args:
        address: 17 Main Street BLACKBURN
```

## How to get the source arguments

Enter your address as the council's [map](https://map.whitehorse.vic.gov.au) property search lists it, e.g. '17 Main Street BLACKBURN'. If several properties match, the address must match one of them exactly.
