# Wingecarribee Shire Council

Support for schedules provided by [Wingecarribee Shire Council](https://www.wsc.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wingecarribee_nsw_gov_au
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
    - name: wingecarribee_nsw_gov_au
      args:
        address: 8 Willow Road, Bowral NSW 2576
```

## How to get the source arguments

Visit the [Wingecarribee Shire Council Bin Collection](https://www.wsc.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection) page and search for your address in the BinDay map. Use the same address format, e.g. "8 Willow Road, Bowral NSW 2576".
