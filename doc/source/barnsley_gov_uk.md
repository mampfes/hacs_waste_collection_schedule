# Barnsley Council

Support for schedules provided by [Barnsley Council](https://wwwapplications.barnsley.gov.uk/wastemvc/ViewCollection/SelectAddress), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: barnsley_gov_uk
      args:
        postcode: POSTCODE
        houseNo: HOUSE NUMBER OR NAME
```

### Configuration Variables

**postcode**  
*(string) (required)*
**houseNo**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: barnsley_gov_uk
      args:
        postcode: S703QN
        houseNo: 1
```

## How to get the source argument

An easy way to discover your Postcode and address used by this service is by going to <https://wwwapplications.barnsley.gov.uk/wastemvc/ViewCollection/SelectAddress> and entering in your address details.
