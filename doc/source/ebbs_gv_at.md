# Gemeinde Ebbs

Support for schedules provided by [Gemeinde Ebbs](https://www.ebbs.gv.at).

Source for Gemeinde Ebbs, Tyrol, Austria waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ebbs_gv_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ebbs_gv_at
      args:
        zone: '1'
```

## How to get the source arguments

Find your street on https://www.ebbs.gv.at/Muellabfuhrtermine to determine your collection zone (1 or 2) -- for example, Tafang is in Zone 2. Residual waste (Restmüllabfuhr) and, in Zone 1, the yellow-bag collection (Gelber Sack) run on a zone-specific schedule; organic waste (Biomüllabfuhr) is the same for both zones.
