# Ards and North Down Borough Council

Support for schedules provided by [Ards and North Down Borough Council](https://ardsandnorthdown.gov.uk).

Source for Ards and North Down Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ardsandnorthdown_gov_uk
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
    - name: ardsandnorthdown_gov_uk
      args:
        uprn: 185833845
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
