# Valorlux

Support for schedules provided by [Valorlux](https://www.valorlux.lu).

Source for Valorlux waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: valorlux_lu
      args:
        commune: COMMUNE
        zone: ZONE
```

### Configuration Variables

**commune**  
*(string) (required)*

**zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: valorlux_lu
      args:
        commune: Mersch
```

## How to get the source arguments

Enter your commune as listed on the Valorlux calendar page, e.g. 'Mersch'. Communes with several collection tours (e.g. 'Luxembourg' with 'Tour 1') also need the zone; a missing or wrong value lists the valid ones.
