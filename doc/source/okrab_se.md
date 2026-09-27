# Ökrab Sophämntning

Support for schedules provided by [Ökrab Sophämntning](https://okrab.se).

Source script for Ökrab waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: okrab_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: okrab_se
      args:
        address: SKOLGATAN 1, S:T OLOF
```
