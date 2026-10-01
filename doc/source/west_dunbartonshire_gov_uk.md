# West Dunbartonshire Council

Support for schedules provided by [West Dunbartonshire Council](https://www.west-dunbarton.gov.uk).

Source for waste collection services from West Dunbartonshire Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: west_dunbartonshire_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: west_dunbartonshire_gov_uk
      args:
        uprn: '129040292'
```

## How to get the source arguments

Find your UPRN by searching your address on https://www.findmyaddress.co.uk/ or by opening the West Dunbartonshire bin collection day page: the UPRN is the number in the page address after `uprn=`.
