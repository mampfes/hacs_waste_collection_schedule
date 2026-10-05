# Brisbane City Council

Support for schedules provided by [Brisbane City Council](https://www.brisbane.qld.gov.au).

Source for Brisbane City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: brisbane_qld_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: brisbane_qld_gov_au
      args:
        suburb: Chapel Hill
        street_name: Moordale St
        street_number: '3'
```
