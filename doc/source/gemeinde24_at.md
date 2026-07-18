# Gemeinde24

Support for schedules provided by [Gemeinde24](https://www.gemeinde24.at).

Source for Gemeinde24 municipal app waste collection data.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gemeinde24_at
      args:
        gemeinde: GEMEINDE
        strasse: STRASSE
```

### Configuration Variables

**gemeinde**  
*(string) (required)*

**strasse**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gemeinde24_at
      args:
        gemeinde: Gaal
        strasse: Gaal
```

## How to get the source arguments

Choose your municipality (Gemeinde), then choose your street/local area (Strasse) from the list that loads for that municipality.
