# Palm Coast, FL

Support for schedules provided by [Palm Coast, FL](https://www.palmcoast.gov).

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
        street: "Ripcord Lane"
```

## How to get the source arguments

Visit the Palm Coast [Solid Waste Collection](https://www.palmcoast.gov/Departments/Solid-Waste-Collection) page. Use your street name (e.g. "Ripcord Lane").
