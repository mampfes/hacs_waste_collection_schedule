# Kirklees Council

Support for schedules provided by [Kirklees Council](https://www.kirklees.gov.uk)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kirklees_gov_uk
      args:
        door_num: 1
        postcode: "HD9 6RJ"
```

### Configuration Variables

**door_num**  
*(string) (required)*

Door number identifier for the property

**postcode**  
*(string) (required)*

Postcode of the property
