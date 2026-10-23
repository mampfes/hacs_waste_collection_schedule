# Cardiff Council

Support for schedules provided by [Cardiff Council](https://www.cardiff.gov.uk).

Source for Cardiff Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cardiff_gov_uk
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
    - name: cardiff_gov_uk
      args:
        uprn: '100100124569'
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and entering your address details.
