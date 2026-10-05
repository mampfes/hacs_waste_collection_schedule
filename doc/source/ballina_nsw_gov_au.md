# Ballina Shire Council

Support for schedules provided by [Ballina Shire Council](https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day).

Source for Ballina Shire Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ballina_nsw_gov_au
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
    - name: ballina_nsw_gov_au
      args:
        address: 1/49 Grant Street BALLINA
```

## How to get the source arguments

Enter the full service address used by Ballina Shire Council, for example '1 Grant St, Ballina NSW 2478'.
