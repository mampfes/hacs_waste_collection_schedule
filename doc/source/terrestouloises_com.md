# Terres Touloises

Support for schedules provided by [Terres Touloises](https://www.terrestouloises.com).

Source script for terrestouloises.com (Communauté de Communes Terres Touloises, France)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: terrestouloises_com
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
    - name: terrestouloises_com
      args:
        commune: Bois-de-Haye
```
