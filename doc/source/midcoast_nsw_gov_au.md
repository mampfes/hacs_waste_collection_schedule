# MidCoast Council

Support for schedules provided by [MidCoast Council](https://www.midcoast.nsw.gov.au/).

Source for MidCoast Council (NSW) rubbish collection.

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
        street_address: 101 Goldens Road, FORSTER
```
