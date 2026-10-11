# Braintree District Council

Support for schedules provided by [Braintree District Council](https://www.braintree.gov.uk).

Braintree District Council, UK - Waste Collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: braintree_gov_uk
      args:
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: braintree_gov_uk
      args:
        house_number: 30
        post_code: CM8 3QE
```

## How to get the source arguments

Enter your postcode and the start of your address as the [council's form](https://www.braintree.gov.uk/xfp/form/554) lists it (usually the house number, or the house name). During the ongoing local government reorganisation (LGR) in Essex, please keep using the source for your current area as long as it still works; new sources for the new North East Essex Council are not expected before April 2028.
