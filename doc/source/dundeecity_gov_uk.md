# Dundee City Council

Support for schedules provided by [Dundee City Council](https://www.dundeecity.gov.uk).

Source script for dundeecity.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dundeecity_gov_uk
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
    - name: dundeecity_gov_uk
      args:
        uprn: 9059046613
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
