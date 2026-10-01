# Marktgemeinde Pernitz

Support for schedules provided by [Marktgemeinde Pernitz](https://www.pernitz.gv.at).

Source for Marktgemeinde Pernitz, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pernitz_gv_at
      args:
        rayon: RAYON
```

### Configuration Variables

**rayon**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pernitz_gv_at
      args:
        rayon: 1
```

## How to get the source arguments

The general waste (Restmüll) collection zone, 1 or 2, that your street belongs to. See the street list at https://pernitz.gv.at/verwaltung/wertstoffsammelstelle-und-muellabfuhr/ to determine your zone.
