# ETRA S.p.A.

Support for schedules provided by [ETRA S.p.A.](https://www.etraspa.it).

Waste collection schedule for ETRA S.p.A. municipalities, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: etraspa_it
      args:
        municipality: MUNICIPALITY
        zone: ZONE
```

### Configuration Variables

**municipality**  
*(string) (optional)*

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

## How to get the source arguments

Choose your municipality and its collection zone as printed on the ETRA calendar: A or B in San Martino di Lupari, C or D in Bassano del Grappa.
