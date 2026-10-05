# Mackay Regional Council

Support for schedules provided by [Mackay Regional Council](https://www.mackay.qld.gov.au).

Source for Mackay Regional Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mackay_qld_gov_au
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
    - name: mackay_qld_gov_au
      args:
        address: 77 Wood Street Mackay
```

## How to get the source arguments

Enter your street address as used on the council's rubbish and bins page (https://www.mackay.qld.gov.au/residents/services/waste), for example '77 Wood Street Mackay'.
