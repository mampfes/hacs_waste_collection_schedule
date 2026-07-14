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

**building_type** *(string) (optional)*: Some addresses (e.g. in Gdynia) have separate schedules for single-family (`single`) and multi-family (`multi`) buildings. Leave empty if your address only has one schedule. If your imported schedule seems to contain duplicate or extra collection dates, try setting this to `single` or `multi` to see which one matches your address on the SmiecioPlan website.

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

```yaml
waste_collection_schedule:
  sources:
    - name: smiecioplan_pl
      args:
        city: "gdynia"
        street: "ŹRÓDŁO MARII"
        house: "19H"
        building_type: "single"
```
