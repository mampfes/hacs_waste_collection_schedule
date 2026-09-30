# Knox City Council

Support for schedules provided by [Knox City Council](https://www.knox.vic.gov.au/).

Source for Knox City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: knox_vic_gov_au
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
    - name: knox_vic_gov_au
      args:
        street_address: 1053 Burwood Highway, FERNTREE GULLY VIC 3156
```

## How to get the source arguments

Enter your address as it appears on [Find my bin days](https://www.knox.vic.gov.au/our-services/bins-rubbish-and-recycling/find-my-bin-days), e.g. '1053 Burwood Highway, FERNTREE GULLY VIC 3156'. The first match is used.
