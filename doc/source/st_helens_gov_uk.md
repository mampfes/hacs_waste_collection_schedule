# St Helens Council

Support for schedules provided by [St Helens Council](https://www.sthelens.gov.uk/article/3473/Check-your-collection-dates/), serving the city of St Helens, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: st_helens_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
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
        postcode: "WA10 1HE"
        uprn: "39079361"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
