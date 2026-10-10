# ETRA S.p.A.

Support for schedules provided by [ETRA S.p.A.](https://www.etraspa.it).

Waste collection schedule for San Martino di Lupari, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: etraspa_it
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: etraspa_it
      args:
        zone: A
```
