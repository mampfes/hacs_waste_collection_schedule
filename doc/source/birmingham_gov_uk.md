# Birmingham City Council

Support for schedules provided by [Birmingham City Council](https://birmingham.gov.uk).

Source for birmingham.gov.uk services for Birmingham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: birmingham_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: birmingham_gov_uk
      args:
        uprn: 100070321799
        postcode: B27 6TF
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details. Enter it together with your postcode.
