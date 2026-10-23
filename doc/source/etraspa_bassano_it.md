# ETRA S.p.A. - Bassano del Grappa

Support for schedules provided by [ETRA S.p.A. - Bassano del Grappa](https://www.etraspa.it).

Waste collection schedule for Bassano del Grappa, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: etraspa_bassano_it
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
    - name: etraspa_bassano_it
      args:
        zone: C
```
