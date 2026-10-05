# Mid-Western Regional Council

Support for schedules provided by [Mid-Western Regional Council](https://www.midwestern.nsw.gov.au/).

Source for Mid-Western Regional Council waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midwestern_nsw_gov_au
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: midwestern_nsw_gov_au
      args:
        area: mudgee_north_monday
```
