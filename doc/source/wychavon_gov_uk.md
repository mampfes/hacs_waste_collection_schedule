# Wychavon District Council (Deprecated)

Support for schedules provided by [Wychavon District Council (Deprecated)](https://wychavon.gov.uk/).

Source for Wychavon District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wychavon_gov_uk
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
    - name: wychavon_gov_uk
      args:
        uprn: 10013938132
```

## How to get the source arguments

Deprecated: use the roundlookup_uk source (council Wychavon) instead. You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
