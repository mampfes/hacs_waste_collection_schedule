# Stadtreinigung Hamburg

Support for schedules provided by [Stadtreinigung Hamburg](https://www.stadtreinigung.hamburg).

Source for Stadtreinigung Hamburg waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        hnId: HNID
        asId: ASID
```

### Configuration Variables

**hnId**  
*(string) (required)*

**asId**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        hnId: 53814
```
