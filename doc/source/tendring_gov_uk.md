# Tendring District Council

Support for schedules provided by [Tendring District Council](https://www.tendringdc.gov.uk).

Source for Tendring District Council, Essex, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tendring_gov_uk
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
    - name: tendring_gov_uk
      args:
        uprn: '100090613962'
```

## How to get the source arguments

Find your UPRN by visiting https://tendring-self.achieveservice.com/en/service/Rubbish_and_recycling_collection_days and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/.
