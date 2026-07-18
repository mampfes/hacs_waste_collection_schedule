# Sutton Council, London

Support for schedules provided by [Sutton Council, London](https://sutton.gov.uk).

Source for Sutton Council, London.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sutton_gov_uk
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sutton_gov_uk
      args:
        id: 4721996
```
