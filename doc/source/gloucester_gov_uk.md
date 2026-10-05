# Gloucester City Council

Support for schedules provided by [Gloucester City Council](https://www.gloucester.gov.uk).

Source for Gloucester City Council, UK, bin collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gloucester_gov_uk
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
    - name: gloucester_gov_uk
      args:
        uprn: 200004478006
```

## How to get the source arguments

Find your UPRN by visiting https://gloucester-self.achieveservice.com/en/service/Bins___Check_your_bin_day and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/.
