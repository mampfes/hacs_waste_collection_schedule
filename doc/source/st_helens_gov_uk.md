# St Helens Council

Support for schedules provided by [St Helens Council](https://sthelens.gov.uk).

Source for sthelens.gov.uk services for St Helens Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: st_helens_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: st_helens_gov_uk
      args:
        postcode: WA9 3AA
        uprn: '39095112'
```

## How to get the source arguments

Enter your postcode and the UPRN of your property. The UPRN is the value of your address in the address list of https://www.sthelens.gov.uk/article/3473/Check-your-collection-dates (browser dev tools), or look it up on https://www.findmyaddress.co.uk/.
