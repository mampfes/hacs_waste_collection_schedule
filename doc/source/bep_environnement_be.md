# Bep-Environnement

Support for schedules provided by [Bep-Environnement](https://www.bep-environnement.be).

Source for Bep Environnement garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bep_environnement_be
      args:
        locality: LOCALITY
```

### Configuration Variables

**locality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bep_environnement_be
      args:
        locality: Dinant
```

## How to get the source arguments

Go to the "https://www.bep-environnement.be" website if you're unsure about your locality.
