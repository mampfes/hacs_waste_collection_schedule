# SmiecioPlan

Support for schedules provided by [SmiecioPlan.pl](https://smiecioplan.pl), Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: smiecioplan_pl
      args:
        city: szczecin
        street: ALEJA WOJSKA POLSKIEGO
        house: "2"
```

### Configuration Variables

**city** *(string) (required)*: City name. Available values: `szczecin`, `gdansk`, `gdynia`, `sopot`.

**street** *(string) (required)*: Street name in uppercase as shown on SmiecioPlan.

**house** *(string) (required)*: House number.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: smiecioplan_pl
      args:
        city: "gdansk"
        street: "ABRAHAMA"
        house: "1"
```
