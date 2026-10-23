# Chesterfield Borough Council

Support for schedules provided by [Chesterfield Borough Council](https://www.chesterfield.gov.uk/).

Source for waste collection services for Chesterfield Borough Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chesterfield_gov_uk
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
    - name: chesterfield_gov_uk
      args:
        uprn: 74023685
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and entering your address details.
