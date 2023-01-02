# Cheshire East Council

Support for schedules provided by [Cheshire East Council](https://online.cheshireeast.gov.uk/mycollectionday/), serving the borough of Cheshire East, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_east_gov_uk
      args:
        uprn: UPRN
```

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_east_gov_uk
      args:
        postcode: POSTCODE
        name_number: NAME OR NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

--- or ---

**postcode**  
*(string) (required)*

**name_number**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_east_gov_uk
      args:
        uprn: 100010132071
```

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_east_gov_uk
      args:
        postcode: WA16 0AY
        name_number: 1
```
