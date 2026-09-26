# Oxford City Council

Support for schedules provided by [Oxford City Council](https://oxford.gov.uk).

Source for oxford.gov.uk services for Oxford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oxford_gov_uk
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
    - name: oxford_gov_uk
      args:
        uprn: '100120827594'
        postcode: OX4 1RB
```

## How to get the source arguments

Go to https://www.oxford.gov.uk/xfp/form/142 and enter your postcode. The UPRN is the option value of your address in the address dropdown (browser dev tools); you can also look it up on https://www.findmyaddress.co.uk/.
