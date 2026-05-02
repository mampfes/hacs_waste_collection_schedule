# Lane Cove Council

Support for schedules provided by [Lane Cove Council](https://www.lanecove.nsw.gov.au/Services/Waste-and-Recycling/Waste-Collection-Calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lanecove_nsw_gov_au
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
    - name: lanecove_nsw_gov_au
      args:
        address: "17 Moore ST LANE COVE WEST, 2066"
```

## How to get the source arguments

Visit the [Lane Cove Council Waste Collection Calendar](https://www.lanecove.nsw.gov.au/Services/Waste-and-Recycling/Waste-Collection-Calendar) and search for your address. Use the exact address shown in the autocomplete result.
