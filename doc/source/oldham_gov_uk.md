# Oldham Council

Support for schedules provided by [Oldham Council](https://oldham.gov.uk/).

Source for Oldham Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oldham_gov_uk
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
    - name: oldham_gov_uk
      args:
        uprn: 422000125973
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and entering your address details.
