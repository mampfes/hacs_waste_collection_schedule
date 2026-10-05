# Wingecarribee Shire Council

Support for schedules provided by [Wingecarribee Shire Council](https://www.wsc.nsw.gov.au).

Source for Wingecarribee Shire Council (NSW) waste collection.

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

Enter the full street address including suburb, state and postcode.
