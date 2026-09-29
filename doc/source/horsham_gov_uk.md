# Horsham District Council

Support for schedules provided by [Horsham District Council](https://www.horsham.gov.uk).

Source script for Horsham District Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: horsham_gov_uk
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
    - name: horsham_gov_uk
      args:
        uprn: 10013792881
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
