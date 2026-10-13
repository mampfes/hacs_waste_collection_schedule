# Canterbury City Council

Support for schedules provided by [Canterbury City Council](https://canterbury.gov.uk).

Source for canterbury.gov.uk services for canterbury

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: canterbury_gov_uk
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
    - name: canterbury_gov_uk
      args:
        post_code: ct68ru
        number: '63'
```

## How to get the source arguments

Enter your postcode and your house number, or your house name if it has no number.
