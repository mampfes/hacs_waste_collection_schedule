# Central Bedfordshire Council

Support for schedules provided by [Central Bedfordshire Council](https://www.centralbedfordshire.gov.uk).

Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: POSTCODE
        house_name: HOUSE_NAME
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: LU6 3PD
        house_name: 1 Buttermere Avenue
```
