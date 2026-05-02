# Maitland City Council

Support for schedules provided by [Maitland City Council](https://www.maitland.nsw.gov.au/residents/bins/bin-collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maitland_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Street address within the Maitland City Council area.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maitland_nsw_gov_au
      args:
        address: 1 High Street, Maitland
```

## How to get the source arguments

Visit the [Maitland City Council Bin Collection](https://www.maitland.nsw.gov.au/residents/bins/bin-collection) page and search for your address in the lookup tool. Use the street address as shown by the lookup.
