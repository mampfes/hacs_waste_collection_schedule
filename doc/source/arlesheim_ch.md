# Gemeinde Arlesheim

Support for schedules provided by [Gemeinde Arlesheim](https://www.arlesheim.ch).

Source for waste collection in Arlesheim, Basel-Landschaft, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: arlesheim_ch
      args:
        kreis: KREIS
```

### Configuration Variables

**kreis**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: arlesheim_ch
      args:
        kreis: West
```

## How to get the source arguments

Pick your collection district (Kreis West: Monday, Kreis Ost: Thursday) from the map in the Abfallkalender PDF.
