# Braintree District Council

Support for schedules provided by [Braintree District Council](https://www.braintree.gov.uk/xfp/form/554), serving Braintree, Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new North East Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

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
        post_code: "CM8 3QE"
        house_number: "30"
```
