# SIDEC

Support for schedules provided by [SIDEC](https://www.sidec.lu).

Source for SIDEC waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sidec_lu
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sidec_lu
      args:
        commune: Parc Hosingen
```

## How to get the source arguments

Enter your commune as listed on the SIDEC website, e.g. 'Mersch'. An unknown commune lists the valid ones.
