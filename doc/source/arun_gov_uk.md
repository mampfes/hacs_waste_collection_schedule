# Arun District Council

Support for schedules provided by [Arun District Council](https://www1.arun.gov.uk/when-are-my-bins-collected), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: arun_gov_uk
      args:
        postcode: POSTCODE
        address: FIRST LINE OF ADDRESS (X, STREET NAME, VILLAGE)
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: arun_gov_uk
      args:
        postcode: BN17 5JA
        address: 21A Beach Road, Littlehampton
```

## Address format

If you see errors retrieving the address, go through the [web flow](https://www1.arun.gov.uk/when-are-my-bins-collected) manually and configure this component with the exact address in the dropdown. The data Arun DC uses to populate this list is quite poorly sanitised in places.
