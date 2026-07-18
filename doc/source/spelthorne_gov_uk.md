# Spelthorne Borough Council

Support for schedules provided by [Spelthorne Borough Council](https://www.spelthorne.gov.uk).

Source for Spelthorne Borough Council, Surrey, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: spelthorne_gov_uk
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
    - name: spelthorne_gov_uk
      args:
        uprn: '33042469'
```

## How to get the source arguments

Find your UPRN by visiting https://spelthorne-self.achieveservice.com/service/Waste_Collections and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/.
