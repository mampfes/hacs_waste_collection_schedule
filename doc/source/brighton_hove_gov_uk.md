# Brighton & Hove City Council

Support for schedules provided by [Brighton & Hove City Council](https://www.brighton-hove.gov.uk/).

Source for Brighton & Hove City Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: brighton_hove_gov_uk
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
    - name: brighton_hove_gov_uk
      args:
        postcode: BN2 0GD
        uprn: '000022064770'
```

## How to get the source arguments

Enter your postcode and your property's UPRN (https://www.findmyaddress.co.uk/). The council only publishes the next couple of weeks. Garden waste is listed only when the property is subscribed.
