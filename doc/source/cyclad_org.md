# Cyclad

Support for schedules provided by [Cyclad](https://cyclad.org).

Source for Cyclad (Charente-Maritime) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org
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
    - name: cyclad_org
      args:
        commune: Nancras
```

## How to get the source arguments

Enter your commune exactly as it is listed in the collection calendar on cyclad.org/les-dechets/collecte/calendrier-de-collecte/ (some towns are split, e.g. "Surgères" and "Surgères centre").
