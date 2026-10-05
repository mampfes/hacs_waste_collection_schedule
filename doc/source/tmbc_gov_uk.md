# Tonbridge and Malling Borough Council

Support for schedules provided by [Tonbridge and Malling Borough Council](https://www.tmbc.gov.uk).

Tonbridge and Malling Borough Council, UK - Waste Collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tmbc_gov_uk
      args:
        post_code: POST_CODE
        address: ADDRESS
```

### Configuration Variables

**post_code**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tmbc_gov_uk
      args:
        address: 138 High Street
        post_code: ME19 6NE
```

## How to get the source arguments

Enter your postcode, and the start of your address as the council's bin collection form lists it (e.g. '138 High Street').
