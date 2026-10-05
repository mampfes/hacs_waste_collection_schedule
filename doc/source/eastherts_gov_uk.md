# East Herts Council

Support for schedules provided by [East Herts Council](https://www.eastherts.gov.uk).

Source for www.eastherts.gov.uk services for East Herts Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastherts_gov_uk
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
    - name: eastherts_gov_uk
      args:
        uprn: '100080738904'
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
