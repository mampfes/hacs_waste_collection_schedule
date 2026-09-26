# Hartlepool Borough Council

Support for schedules provided by [Hartlepool Borough Council](https://www.hartlepool.gov.uk).

Source for www.hertlepool.gov.uk services for Hartlepool Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hartlepool_gov_uk
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
    - name: hartlepool_gov_uk
      args:
        uprn: '100110021946'
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
