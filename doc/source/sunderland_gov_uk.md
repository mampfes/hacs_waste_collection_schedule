# Sunderland City Council

Support for schedules provided by [Sunderland City Council](https://www.sunderland.gov.uk/bindays), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sunderland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
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
    - name: sunderland_gov_uk
      args:
        postcode: "SR4 8RJ"
        address: "17, Sutherland Drive"
```
