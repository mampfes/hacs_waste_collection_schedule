# Adur & Worthing Councils

Support for schedules provided by [Adur & Worthing Councils](https://www.adur-worthing.gov.uk/bin-day/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: adur_worthing_gov_uk
      args:
        postcode: POSTCODE
        address: FIRST LINE OF ADDRESS (X, STREET NAME)
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
    - name: adur_worthing_gov_uk
      args:
        postcode: BN15 9UX
        address: 1 Western Road
```
