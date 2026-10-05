# Herefordshire City Council

Support for schedules provided by [Herefordshire City Council](https://herefordshire.gov.uk).

Source for herefordshire.gov.uk services for hereford

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: herefordshire_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: herefordshire_gov_uk
      args:
        post_code: hr49js
        number: '52'
```

## How to get the source arguments

Enter the postcode and the house number, house name or UPRN (Unique Property Reference Number) of the property. If your property only has a name and no number, enter the name; if it is still not found, the error message lists the full addresses found for your postcode so you can copy the UPRN or exact wording from there.
