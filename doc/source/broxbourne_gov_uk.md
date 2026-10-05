# Borough of Broxbourne Council

Support for schedules provided by [Borough of Broxbourne Council](https://www.broxbourne.gov.uk).

Source for broxbourne.gov.uk services for Broxbourne, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: broxbourne_gov_uk
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
    - name: broxbourne_gov_uk
      args:
        uprn: '148040092'
        postcode: EN10 7PX
```

## How to get the source arguments

Go to https://www.broxbourne.gov.uk/bin-collection-date and enter your postcode. The UPRN is the option value of your address in the address dropdown (browser dev tools); you can also look it up on https://www.findmyaddress.co.uk/.
