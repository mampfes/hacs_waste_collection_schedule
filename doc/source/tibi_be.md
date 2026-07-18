# Tibi (Charleroi region)

Support for schedules provided by [Tibi (Charleroi region)](https://www.tibi.be).

Selective waste collection schedule for the Tibi intercommunale (Charleroi region, Wallonia).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tibi_be
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
    - name: tibi_be
      args:
        commune: Charleroi
```

## How to get the source arguments

Enter your commune exactly as it appears in the Tibi calendar (e.g. 'Charleroi', 'Couillet', 'Marcinelle'). Larger municipalities are split into numbered sectors (e.g. 'Courcelles 1').
