# Borough Council of King's Lynn & West Norfolk

Support for schedules provided by [Borough Council of King's Lynn & West Norfolk](https://www.west-norfolk.gov.uk).

Source for www.west-norfolk.gov.uk services for Borough Council of King's Lynn & West Norfolk, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: west_norfolk_gov_uk
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
    - name: west_norfolk_gov_uk
      args:
        uprn: '100090969937'
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
