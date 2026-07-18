# Epping Forest District Council

Support for schedules provided by [Epping Forest District Council](https://www.eppingforestdc.gov.uk).

Source for Epping Forest District Council, Essex, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eppingforestdc_gov_uk
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
    - name: eppingforestdc_gov_uk
      args:
        uprn: '100090495060'
```

## How to get the source arguments

Find your UPRN by visiting https://eppingforestdc-self.achieveservice.com/service/Check_your_collection_day and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/.
