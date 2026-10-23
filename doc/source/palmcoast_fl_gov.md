# Palm Coast, FL

Support for schedules provided by [Palm Coast, FL](https://www.palmcoast.gov).

Source for Palm Coast, FL waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: palmcoast_fl_gov
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: palmcoast_fl_gov
      args:
        street: Ripcord Lane
```
