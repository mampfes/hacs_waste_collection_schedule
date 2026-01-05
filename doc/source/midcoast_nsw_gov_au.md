# MidCoast Council

Support for schedules provided by [MidCoast Council](https://www.midcoast.nsw.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midcoast_nsw_gov_au
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
    - name: midcoast_nsw_gov_au
      args:
        street_address: 101 Golds Road, FORSTER
```

## How to get the source arguments

Visit the [MidCoast Council Your Bin Service](https://www.midcoast.nsw.gov.au/Services/Waste-and-recycling/When-is-my-bin-collected) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
