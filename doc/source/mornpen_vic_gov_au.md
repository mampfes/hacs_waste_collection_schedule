# Mornington Peninsula Shire Council

Support for schedules provided by [YMornington Peninsula Shire Council](https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mornpen_vic_gov_au
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
    - name: mornpen_vic_gov_au
      args:
        street_address: 3649 Frankston-Flinders Rd, Merricks VIC 3916
```

## How to get the source arguments

Visit the [Mornington Peninsula Shire Council](https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
