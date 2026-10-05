# Sysav Sophämntning

Support for schedules provided by [Sysav Sophämntning](https://www.sysav.se).

Source for Sysav waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sysav_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sysav_se
      args:
        street_address: Sommargatan 1, Svedala
```
