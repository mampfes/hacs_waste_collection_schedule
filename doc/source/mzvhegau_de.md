# MZV Hegau

Support for schedules provided by [MZV Hegau](https://www.mzvhegau.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mzvhegau_de
      args:
        city: CITY
```

### Configuration Variables

**city**  
*(string) (required)*

Your city or municipality name in the MZV Hegau service area, e.g. `Engen`, `Singen`.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: mzvhegau_de
      args:
        city: "Engen"
```
