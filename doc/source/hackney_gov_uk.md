# London Borough of Hackney

Support for schedules provided by [London Borough of Hackney](https://www.hackney.gov.uk/).

Source for London Borough of Hackney Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hackney_gov_uk
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
    - name: hackney_gov_uk
      args:
        uprn: '100021058914'
        postcode: E8 4LL
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and enter it together with the postcode of the property.
