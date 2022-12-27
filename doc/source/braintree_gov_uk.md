# Braintree District Council

Support for schedules provided by [Braintree District Council](https://www.braintree.gov.uk/xfp/form/554), serving Braintree, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: braintree_gov_uk
      args:
        post_code: Post Code
        house_number: House Number
```

### Configuration Variables

**post_code**<br>
*(string) (required)*

**house_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: braintree_gov_uk
      args:
        post_code: "CM8 3QE"
        house_number: "30"
```
