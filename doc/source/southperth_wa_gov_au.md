# City of South Perth

Support for schedules provided by [City of South Perth](https://southperth.wa.gov.au/residents/home-and-neighbourhood/see-what's-near-me).

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

Visit the [City of South Perth](https://southperth.wa.gov.au/residents/home-and-neighbourhood/see-what's-near-me) and search for your address. The address should match the format used in the lookup, e.g. "156 Lansdowne Road KENSINGTON".
