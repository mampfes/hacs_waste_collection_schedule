# City of South Perth

Support for schedules provided by [City of South Perth](https://southperth.wa.gov.au).

Source for City of South Perth waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southperth_wa_gov_au
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
    - name: southperth_wa_gov_au
      args:
        address: 156 Lansdowne Road KENSINGTON
```

## How to get the source arguments

Enter your street address including suburb (e.g. '156 Lansdowne Road KENSINGTON').
