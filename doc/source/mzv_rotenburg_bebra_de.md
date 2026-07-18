# MZV Rotenburg

Support for schedules provided by [MZV Rotenburg](https://www.mzv-rotenburg-bebra.de).

Source for MZV Rotenburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mzv_rotenburg_bebra_de
      args:
        city: CITY
        yellow_route: YELLOW_ROUTE
        paper_route: PAPER_ROUTE
```

### Configuration Variables

**city**  
*(string) (required)*

**yellow_route**  
*(string) (optional)*

**paper_route**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mzv_rotenburg_bebra_de
      args:
        city: rote
```

## How to get the source arguments

Der Ort muss genau wie im `ort`-URL-Parameter der Links auf https://www.mzv-rotenburg-bebra.de//webapp.html geschrieben werden (z.B. `rote`, `bebra`). yellow_route / paper_route filtern nach Sammelroute, falls der Ort mehrere Routen hat.
