# Gemeinde Felixdorf

Support for schedules provided by [Gemeinde Felixdorf](https://www.felixdorf.gv.at).

Source for Gemeinde Felixdorf, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: felixdorf_gv_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: felixdorf_gv_at
      args:
        zone: Rayon 1
```

## How to get the source arguments

Select your collection zone (Rayon 1 or Rayon 2). Leave blank to receive all zones.
